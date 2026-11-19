import base64
import json
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import device_id, get_lang, optional_user
from app.core.config import settings
from app.db import get_db
from app.models import AIMediaJob, AIMessage, AISession, AIUsage, Place, User
from app.models.types import utcnow
from app.schemas.ai_admin import (
    ChatIn,
    ChatOut,
    CitationOut,
    FeedbackIn,
    ImageIn,
    ImageOut,
    VoiceIn,
    VoiceOut,
)
from app.services import ai_limits, rag
from app.services.ai_limits import today
from app.services.ai_providers import stt_provider, tts_provider, vision_provider
from app.services.settings_store import get_setting

router = APIRouter(prefix="/ai", tags=["ai"])

MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB per TZ section 7


def _remaining(db: Session, subject: str, registered: bool) -> int:
    key = "ai_limit_registered" if registered else "ai_limit_anonymous"
    limit = get_setting(db, key) or getattr(settings, key)
    row = db.scalar(select(AIUsage).where(AIUsage.subject == subject, AIUsage.day == today()))
    return max(0, limit - (row.count if row else 0))


def _can_synthesize_tts(db: Session, lang: str) -> bool:
    if lang == "kaa":
        return bool(get_setting(db, "kaa_tts_enabled", False))
    return lang in settings.supported_langs


def purge_expired_media(db: Session) -> int:
    """Purge tourist photos/media older than 24 hours (NF-09, AC-11)."""
    now = utcnow()
    expired = db.scalars(
        select(AIMediaJob).where(AIMediaJob.status != "purged", AIMediaJob.expires_at <= now)
    ).all()
    for job in expired:
        job.storage_key = None
        job.status = "purged"
        job.purged_at = now
    if expired:
        db.flush()
    return len(expired)


@router.post("/chat", response_model=ChatOut)
def chat(
    body: ChatIn,
    stream: bool = Query(default=False),
    lang: str = Depends(get_lang),
    device: str = Depends(device_id),
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
):
    effective_lang = body.lang if body.lang in settings.supported_langs else lang
    if body.place_id is not None and db.get(Place, body.place_id) is None:
        raise HTTPException(404, "place_not_found")
    subject = f"user:{user.id}" if user else f"device:{device}"
    ai_limits.check_and_consume(db, subject, registered=user is not None)

    answer = rag.answer_question(db, body.question, effective_lang, body.place_id)

    session = AISession(
        device_id=device,
        user_id=user.id if user else None,
        place_id=body.place_id,
        lang=effective_lang,
    )
    db.add(session)
    db.flush()
    db.add(AIMessage(session_id=session.id, role="user", text=body.question))
    msg = AIMessage(
        session_id=session.id,
        role="assistant",
        text=answer.text,
        grounded=answer.grounded,
        cost_usd=answer.cost_usd,
        citations=[c.__dict__ for c in answer.citations],
    )
    db.add(msg)
    db.commit()

    out = ChatOut(
        message_id=msg.id,
        answer=answer.text,
        grounded=answer.grounded,
        citations=[CitationOut(**c.__dict__) for c in answer.citations],
        lang=effective_lang,
        remaining_today=_remaining(db, subject, user is not None),
    )
    if stream:
        def _sse():
            for word in out.answer.split(" "):
                yield f"event: token\ndata: {json.dumps({'token': word + ' '})}\n\n"
            yield f"event: done\ndata: {out.model_dump_json()}\n\n"

        return StreamingResponse(_sse(), media_type="text/event-stream")
    return out


@router.post("/voice", response_model=VoiceOut)
def voice(
    body: VoiceIn,
    lang: str = Depends(get_lang),
    device: str = Depends(device_id),
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
):
    effective_lang = body.lang if body.lang in settings.supported_langs else lang
    enabled_langs = get_setting(db, "voice_enabled_langs") or ["uz", "ru", "en"]
    if effective_lang not in enabled_langs:
        raise HTTPException(422, f"voice_disabled_for_lang:{effective_lang}")
    if body.place_id is not None and db.get(Place, body.place_id) is None:
        raise HTTPException(404, "place_not_found")

    subject = f"user:{user.id}" if user else f"device:{device}"
    ai_limits.check_and_consume(db, subject, registered=user is not None)

    try:
        raw_audio = base64.b64decode(body.audio_base64) if body.audio_base64 else b""
    except Exception as exc:
        raise HTTPException(422, "invalid_audio_base64") from exc

    transcript = stt_provider.transcribe(raw_audio, effective_lang, body.transcript_hint)
    if len(transcript.strip()) < 2:
        raise HTTPException(422, "empty_transcript")

    answer = rag.answer_question(db, transcript, effective_lang, body.place_id)
    audio_url = (
        tts_provider.synthesize(answer.text, effective_lang)
        if _can_synthesize_tts(db, effective_lang)
        else None
    )

    session = AISession(
        device_id=device,
        user_id=user.id if user else None,
        place_id=body.place_id,
        lang=effective_lang,
    )
    db.add(session)
    db.flush()
    db.add(AIMessage(session_id=session.id, role="user", text=transcript))
    msg = AIMessage(
        session_id=session.id,
        role="assistant",
        text=answer.text,
        grounded=answer.grounded,
        cost_usd=answer.cost_usd,
        citations=[c.__dict__ for c in answer.citations],
    )
    db.add(msg)
    db.commit()
    return VoiceOut(
        message_id=msg.id,
        transcript=transcript,
        answer=answer.text,
        audio_url=audio_url,
        grounded=answer.grounded,
        citations=[CitationOut(**c.__dict__) for c in answer.citations],
        lang=effective_lang,
        remaining_today=_remaining(db, subject, user is not None),
    )


@router.post("/image", response_model=ImageOut)
def image(
    body: ImageIn,
    lang: str = Depends(get_lang),
    device: str = Depends(device_id),
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
):
    purge_expired_media(db)
    effective_lang = body.lang if body.lang in settings.supported_langs else lang
    if body.place_id is not None and db.get(Place, body.place_id) is None:
        raise HTTPException(404, "place_not_found")

    try:
        raw_image = base64.b64decode(body.image_base64, validate=True) if body.image_base64 else b""
    except Exception as exc:
        raise HTTPException(422, "invalid_image_base64") from exc

    if len(raw_image) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "image_too_large")
    if not raw_image and not body.ocr_hint.strip():
        raise HTTPException(422, "image_or_ocr_hint_required")

    subject = f"user:{user.id}" if user else f"device:{device}"
    ai_limits.check_and_consume(db, subject, registered=user is not None)

    vis = vision_provider.analyze(raw_image, body.ocr_hint)
    answer = rag.answer_question(db, vis.ocr_text, effective_lang, body.place_id)
    audio_url = (
        tts_provider.synthesize(answer.text, effective_lang)
        if _can_synthesize_tts(db, effective_lang)
        else None
    )

    session = AISession(
        device_id=device,
        user_id=user.id if user else None,
        place_id=body.place_id,
        lang=effective_lang,
    )
    db.add(session)
    db.flush()
    db.add(AIMessage(session_id=session.id, role="user", text=f"[image] {vis.ocr_text}"))
    msg = AIMessage(
        session_id=session.id,
        role="assistant",
        text=answer.text,
        grounded=answer.grounded,
        cost_usd=answer.cost_usd,
        citations=[c.__dict__ for c in answer.citations],
    )
    db.add(msg)
    expires = utcnow() + timedelta(hours=24)
    job = AIMediaJob(
        session_id=session.id,
        device_id=device,
        kind="image",
        lang=effective_lang,
        storage_key=f"ephemeral/photos/{session.id}.jpg",
        size_bytes=len(raw_image),
        exif_stripped=vis.exif_stripped,
        ocr_text=vis.ocr_text,
        answer_text=answer.text,
        audio_url=audio_url,
        status="completed",
        expires_at=expires,
    )
    db.add(job)
    db.commit()
    return ImageOut(
        job_id=job.id,
        message_id=msg.id,
        ocr_text=vis.ocr_text,
        answer=answer.text,
        audio_url=audio_url,
        grounded=answer.grounded,
        citations=[CitationOut(**c.__dict__) for c in answer.citations],
        exif_stripped=vis.exif_stripped,
        expires_at=job.expires_at,
        lang=effective_lang,
        remaining_today=_remaining(db, subject, user is not None),
    )


@router.post("/media/purge")
def purge_media(db: Session = Depends(get_db)):
    purged = purge_expired_media(db)
    db.commit()
    return {"purged": purged}


@router.post("/messages/{message_id}/feedback", status_code=204)
def feedback(
    message_id: UUID,
    body: FeedbackIn,
    device: str = Depends(device_id),
    db: Session = Depends(get_db),
):
    msg = db.get(AIMessage, message_id)
    session = db.get(AISession, msg.session_id) if msg else None
    if msg is None or msg.role != "assistant" or session.device_id != device:
        raise HTTPException(404, "message_not_found")
    if body.feedback is not None:
        msg.feedback = body.feedback
    if body.error_report is not None:
        msg.error_report = body.error_report
    db.commit()
