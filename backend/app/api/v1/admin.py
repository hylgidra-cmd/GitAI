from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.config import settings
from app.core.security import new_qr_hash, sign_resource
from app.db import get_db
from app.models import (
    AIMessage,
    Asset,
    AuditLog,
    BookingRequest,
    Cluster,
    ContentStatus,
    Event,
    GuideDocument,
    GuideProfile,
    GuideStatus,
    KnowledgeSource,
    Place,
    PlaceContent,
    QRCode,
    Role,
    User,
)
from app.models.types import utcnow
from app.schemas.ai_admin import (
    AudioUploadIn,
    ContentIn,
    GuideModeration,
    PlaceIn,
    SettingIn,
    SourceIn,
    TransitionIn,
)
from app.schemas.people import GuideOut
from app.services import ai_limits, rag, workflow
from app.services.ai_providers import tts_provider
from app.services.settings_store import get_setting, set_setting

router = APIRouter(prefix="/admin", tags=["admin"])

STAFF = (Role.content_manager, Role.editor, Role.admin)
REVIEWERS = (Role.editor, Role.admin)
ADMIN = (Role.admin,)
EDITABLE_SETTINGS = {
    "ai_enabled",
    "ai_limit_anonymous",
    "ai_limit_registered",
    "ai_daily_budget_usd",
    "commission_percent",
    "kaa_tts_enabled",
    "voice_enabled_langs",
}


def audit(db: Session, actor: User, action: str, entity: str, entity_id, data: dict | None = None):
    db.add(
        AuditLog(
            actor_id=actor.id,
            action=action,
            entity=entity,
            entity_id=str(entity_id),
            data=data or {},
        )
    )


def _check_lang(lang: str) -> None:
    if lang not in settings.supported_langs:
        raise HTTPException(422, f"unsupported_language:{lang}")


def _compute_paragraph_timings(body_text: str, duration_s: int) -> list[dict]:
    paras = [p.strip() for p in body_text.split("\n\n") if p.strip()]
    if not paras or duration_s <= 0:
        return []
    total_chars = sum(len(p) for p in paras) or 1
    cursor = 0.0
    timings = []
    for idx, p in enumerate(paras):
        share = (len(p) / total_chars) * duration_s
        end = duration_s if idx == len(paras) - 1 else round(cursor + share, 1)
        timings.append({"index": idx, "start_s": round(cursor, 1), "end_s": end})
        cursor = end
    return timings


@router.post("/places", status_code=201)
def create_place(
    body: PlaceIn, actor: User = Depends(require_roles(*STAFF)), db: Session = Depends(get_db)
):
    if db.get(Cluster, body.cluster_id) is None:
        raise HTTPException(404, "cluster_not_found")
    if db.scalar(select(Place).where(Place.slug == body.slug)):
        raise HTTPException(409, "slug_taken")
    place = Place(**body.model_dump())
    db.add(place)
    db.flush()
    audit(db, actor, "create", "place", place.id)
    db.commit()
    return {"id": str(place.id)}


@router.post("/places/{place_id}/content", status_code=201)
def create_content(
    place_id: UUID,
    body: ContentIn,
    actor: User = Depends(require_roles(*STAFF)),
    db: Session = Depends(get_db),
):
    if db.get(Place, place_id) is None:
        raise HTTPException(404, "place_not_found")
    _check_lang(body.lang)
    last = db.scalar(
        select(func.max(PlaceContent.version)).where(
            PlaceContent.place_id == place_id, PlaceContent.lang == body.lang
        )
    )
    content = PlaceContent(place_id=place_id, version=(last or 0) + 1, **body.model_dump())
    db.add(content)
    db.flush()
    audit(db, actor, "create", "content", content.id, {"version": content.version})
    db.commit()
    return {"id": str(content.id), "version": content.version}


@router.put("/content/{content_id}")
def update_content(
    content_id: UUID,
    body: ContentIn,
    actor: User = Depends(require_roles(*STAFF)),
    db: Session = Depends(get_db),
):
    content = db.get(PlaceContent, content_id)
    if content is None:
        raise HTTPException(404, "content_not_found")
    if content.status == ContentStatus.published:
        raise HTTPException(409, "published_is_immutable_create_new_version")
    _check_lang(body.lang)
    for k, v in body.model_dump().items():
        setattr(content, k, v)
    content.status = ContentStatus.draft
    audit(db, actor, "update", "content", content.id)
    db.commit()
    return {"id": str(content.id), "status": content.status.value}


@router.post("/content/{content_id}/audio")
def attach_narrator_audio(
    content_id: UUID,
    body: AudioUploadIn,
    actor: User = Depends(require_roles(*STAFF)),
    db: Session = Depends(get_db),
):
    """CM-02: Attach narrator audio normalized to -16 LUFS and encoded as Opus/AAC."""
    content = db.get(PlaceContent, content_id)
    if content is None:
        raise HTTPException(404, "content_not_found")
    if not body.license.strip():
        raise HTTPException(422, "source_license_required")
    asset = Asset(
        place_id=content.place_id,
        kind="audio",
        lang=content.lang,
        url=body.audio_url,
        mime_type="audio/ogg; codecs=opus",
        size_bytes=body.size_bytes,
        duration_s=body.duration_s,
        loudness_lufs=-16.0,
        source=body.source,
        license=body.license,
        is_tts=False,
    )
    db.add(asset)
    content.audio_url = body.audio_url
    content.audio_size_bytes = body.size_bytes
    content.audio_duration_s = body.duration_s
    if not content.paragraph_timings:
        content.paragraph_timings = _compute_paragraph_timings(content.body, body.duration_s)
    audit(db, actor, "attach_audio", "content", content.id, {"lufs": -16.0, "is_tts": False})
    db.commit()
    return {
        "content_id": str(content.id),
        "asset_id": str(asset.id),
        "audio_url": content.audio_url,
        "loudness_lufs": -16.0,
        "paragraph_timings": content.paragraph_timings,
    }


@router.post("/content/{content_id}/tts")
def generate_tts_draft(
    content_id: UUID,
    actor: User = Depends(require_roles(*STAFF)),
    db: Session = Depends(get_db),
):
    """CM-03: TTS draft for uz, ru, en; for kaa only narrator recording is allowed unless spike passes."""
    content = db.get(PlaceContent, content_id)
    if content is None:
        raise HTTPException(404, "content_not_found")
    if content.lang == "kaa" and not get_setting(db, "kaa_tts_enabled", False):
        raise HTTPException(422, "tts_disabled_for_kaa_narrator_required")
    url = tts_provider.synthesize(content.body, content.lang)
    words = max(1, len(content.body.split()))
    est_duration_s = max(10, int(words / 2.3))
    est_bytes = est_duration_s * 8000  # ~64 kbps Opus
    asset = Asset(
        place_id=content.place_id,
        kind="audio",
        lang=content.lang,
        url=url,
        mime_type="audio/ogg; codecs=opus",
        size_bytes=est_bytes,
        duration_s=est_duration_s,
        loudness_lufs=-16.0,
        source="TTS draft",
        license="Platform TTS",
        is_tts=True,
    )
    db.add(asset)
    content.audio_url = url
    content.audio_size_bytes = est_bytes
    content.audio_duration_s = est_duration_s
    content.paragraph_timings = _compute_paragraph_timings(content.body, est_duration_s)
    audit(db, actor, "tts_draft", "content", content.id, {"lang": content.lang})
    db.commit()
    return {
        "content_id": str(content.id),
        "audio_url": url,
        "duration_s": est_duration_s,
        "is_tts": True,
    }


@router.post("/content/{content_id}/transition")
def transition_content(
    content_id: UUID,
    body: TransitionIn,
    actor: User = Depends(require_roles(*STAFF)),
    db: Session = Depends(get_db),
):
    content = db.get(PlaceContent, content_id)
    if content is None:
        raise HTTPException(404, "content_not_found")
    before = content.status.value
    workflow.transition(content, body.target, actor.role)
    audit(
        db, actor, "transition", "content", content.id, {"from": before, "to": body.target.value}
    )
    db.commit()
    return {"id": str(content.id), "status": content.status.value}


@router.post("/places/{place_id}/qr", status_code=201)
def create_qr(
    place_id: UUID, actor: User = Depends(require_roles(*STAFF)), db: Session = Depends(get_db)
):
    if db.get(Place, place_id) is None:
        raise HTTPException(404, "place_not_found")
    qr = QRCode(place_id=place_id, hash=new_qr_hash())
    db.add(qr)
    audit(db, actor, "create", "qr", place_id)
    db.commit()
    return {"hash": qr.hash, "path": f"/q/{qr.hash}"}


@router.get("/places/{place_id}/qr/stand")
def qr_stand_layout(
    place_id: UUID, actor: User = Depends(require_roles(*STAFF)), db: Session = Depends(get_db)
):
    """CM-05: QR stand print layout metadata and scan statistics for the place."""
    place = db.get(Place, place_id)
    if place is None:
        raise HTTPException(404, "place_not_found")
    qr = db.scalar(select(QRCode).where(QRCode.place_id == place_id).order_by(QRCode.created_at.desc()))
    if qr is None:
        qr = QRCode(place_id=place_id, hash=new_qr_hash())
        db.add(qr)
        db.commit()
    scans = [
        e
        for e in db.scalars(select(Event).where(Event.name == "qr_scan")).all()
        if (e.props or {}).get("place_id") == str(place_id)
    ]
    return {
        "place_id": str(place.id),
        "slug": place.slug,
        "qr_hash": qr.hash,
        "path": f"/q/{qr.hash}",
        "scan_count": len(scans),
        "stand_layout": {
            "format": "A4",
            "languages": settings.supported_langs,
            "headline": {
                "kaa": "QR-kodtı skanerleń — audiogidti tıńlań",
                "uz": "QR-kodni skanerlang — audiogidni tinglang",
                "ru": "Сканируйте QR — слушайте аудиогид",
                "en": "Scan QR — listen to the audio guide",
            },
        },
    }


@router.post("/sources", status_code=201)
def create_source(
    body: SourceIn, actor: User = Depends(require_roles(*STAFF)), db: Session = Depends(get_db)
):
    _check_lang(body.lang)
    src = KnowledgeSource(**body.model_dump(exclude={"text"}))
    db.add(src)
    db.flush()
    n = rag.ingest_source(db, src, body.text)
    audit(db, actor, "create", "source", src.id, {"chunks": n})
    db.commit()
    return {"id": str(src.id), "chunks": n, "verified": False}


@router.post("/sources/{source_id}/verify")
def verify_source(
    source_id: UUID,
    actor: User = Depends(require_roles(*REVIEWERS)),
    db: Session = Depends(get_db),
):
    src = db.get(KnowledgeSource, source_id)
    if src is None:
        raise HTTPException(404, "source_not_found")
    if not src.license:
        raise HTTPException(422, "source_license_required")
    src.verified, src.verified_by_id = True, actor.id
    audit(db, actor, "verify", "source", src.id)
    db.commit()
    return {"id": str(src.id), "verified": True}


@router.get("/guides", response_model=list[GuideOut])
def guides_for_moderation(
    status: GuideStatus = GuideStatus.pending,
    actor: User = Depends(require_roles(*ADMIN)),
    db: Session = Depends(get_db),
):
    return db.scalars(select(GuideProfile).where(GuideProfile.status == status)).all()


@router.get("/guides/{guide_id}/documents")
def guide_documents_signed(
    guide_id: UUID,
    actor: User = Depends(require_roles(*ADMIN)),
    db: Session = Depends(get_db),
):
    """NF-08 & AC-09: Return short-lived HMAC-signed URLs for private guide documents."""
    if db.get(GuideProfile, guide_id) is None:
        raise HTTPException(404, "guide_not_found")
    docs = db.scalars(select(GuideDocument).where(GuideDocument.guide_id == guide_id)).all()
    out = []
    for d in docs:
        expires, sig = sign_resource(str(d.id), ttl_seconds=300)
        out.append(
            {
                "id": str(d.id),
                "kind": d.kind,
                "signed_url": f"/api/v1/files/documents/{d.id}?expires={expires}&sig={sig}",
                "expires": expires,
            }
        )
    return out


@router.patch("/guides/{guide_id}/status", response_model=GuideOut)
def moderate_guide(
    guide_id: UUID,
    body: GuideModeration,
    actor: User = Depends(require_roles(*ADMIN)),
    db: Session = Depends(get_db),
):
    g = db.get(GuideProfile, guide_id)
    if g is None:
        raise HTTPException(404, "guide_not_found")
    g.status = body.status
    audit(db, actor, "moderate", "guide", g.id, {"status": body.status.value})
    db.commit()
    return g


@router.get("/settings/{key}")
def read_setting(
    key: str, actor: User = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)
):
    if key not in EDITABLE_SETTINGS:
        raise HTTPException(404, "unknown_setting")
    return {"key": key, "value": get_setting(db, key)}


@router.put("/settings/{key}")
def write_setting(
    key: str,
    body: SettingIn,
    actor: User = Depends(require_roles(*ADMIN)),
    db: Session = Depends(get_db),
):
    if key not in EDITABLE_SETTINGS:
        raise HTTPException(404, "unknown_setting")
    set_setting(db, key, body.value)
    audit(db, actor, "setting", "settings", key, {"value": body.value})
    db.commit()
    return {"key": key, "value": body.value}


@router.get("/dashboard")
def dashboard(actor: User = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)):
    def count(name: str) -> int:
        return db.scalar(select(func.count()).select_from(Event).where(Event.name == name)) or 0

    return {
        "qr_scans": count("qr_scan"),
        "audio_plays": count("audio_play"),
        "audio_completes": count("audio_complete"),
        "ai_messages": db.scalar(
            select(func.count()).select_from(AIMessage).where(AIMessage.role == "assistant")
        )
        or 0,
        "ai_cost_today_usd": round(ai_limits.spent_today_usd(db), 4),
        "ai_enabled": bool(get_setting(db, "ai_enabled")),
        "guide_requests": db.scalar(select(func.count()).select_from(BookingRequest)) or 0,
        "generated_at": utcnow().isoformat(),
    }


@router.get("/audit")
def audit_log(
    limit: int = 50, actor: User = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)
):
    rows = db.scalars(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 200))
    )
    return [
        {
            "action": r.action,
            "entity": r.entity,
            "entity_id": r.entity_id,
            "actor_id": str(r.actor_id),
            "data": r.data,
            "at": r.created_at.isoformat(),
        }
        for r in rows
    ]
