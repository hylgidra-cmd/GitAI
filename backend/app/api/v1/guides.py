from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.config import settings
from app.db import get_db
from app.models import (
    BookingRequest,
    GuideDocument,
    GuideProfile,
    GuideStatus,
    RequestStatus,
    Role,
    User,
)
from app.models.types import utcnow
from app.schemas.people import (
    DocumentIn,
    GuideIn,
    GuideOut,
    RequestDecision,
    RequestIn,
    RequestOut,
)
from app.services.notify import notifier

router = APIRouter(tags=["guides"])


def _expire_overdue(db: Session, stmt_rows: list[BookingRequest]) -> None:
    now = utcnow()
    for r in stmt_rows:
        if r.status == RequestStatus.pending and r.respond_by < now:
            r.status = RequestStatus.expired
    db.flush()


@router.get("/guides", response_model=list[GuideOut])
def list_guides(
    lang: str | None = None,
    specialty: str | None = None,
    has_4x4: bool | None = None,
    max_price: float | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(GuideProfile).where(GuideProfile.status == GuideStatus.approved)
    if has_4x4 is not None:
        stmt = stmt.where(GuideProfile.has_4x4 == has_4x4)
    if max_price is not None:
        stmt = stmt.where(GuideProfile.price_from_usd <= max_price)
    guides = db.scalars(stmt.order_by(GuideProfile.rating.desc())).all()
    if lang:
        guides = [g for g in guides if lang in g.languages]
    if specialty:
        guides = [g for g in guides if specialty in g.specialties]
    return guides


@router.put("/guides/me", response_model=GuideOut)
def upsert_my_profile(
    body: GuideIn, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    bad = [x for x in body.languages if x not in settings.supported_langs]
    if bad:
        raise HTTPException(422, f"unsupported_languages:{','.join(bad)}")
    profile = db.scalar(select(GuideProfile).where(GuideProfile.user_id == user.id))
    if profile is None:
        profile = GuideProfile(user_id=user.id, **body.model_dump())
        db.add(profile)
        if user.role == Role.tourist:
            user.role = Role.guide
    else:
        for k, v in body.model_dump().items():
            setattr(profile, k, v)
        if profile.status == GuideStatus.approved:  # edits require re-moderation
            profile.status = GuideStatus.pending
    db.commit()
    return profile


@router.post("/guides/me/documents", status_code=201)
def add_document(
    body: DocumentIn, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    profile = db.scalar(select(GuideProfile).where(GuideProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(404, "guide_profile_required")
    doc = GuideDocument(guide_id=profile.id, kind=body.kind, storage_key=body.storage_key)
    db.add(doc)
    db.commit()
    return {"id": str(doc.id)}


@router.get("/guides/{guide_id}", response_model=GuideOut)
def guide_detail(guide_id: UUID, db: Session = Depends(get_db)):
    g = db.get(GuideProfile, guide_id)
    if g is None or g.status != GuideStatus.approved:
        raise HTTPException(404, "guide_not_found")
    return g


@router.post("/guides/{guide_id}/requests", response_model=RequestOut, status_code=201)
def create_request(
    guide_id: UUID,
    body: RequestIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    g = db.get(GuideProfile, guide_id)
    if g is None or g.status != GuideStatus.approved:
        raise HTTPException(404, "guide_not_found")
    if g.user_id == user.id:
        raise HTTPException(409, "cannot_book_self")
    if body.date_to < body.date_from or body.date_from < utcnow().date():
        raise HTTPException(422, "invalid_dates")
    req = BookingRequest(
        guide_id=g.id,
        tourist_id=user.id,
        route_id=body.route_id,
        date_from=body.date_from,
        date_to=body.date_to,
        group_size=body.group_size,
        message=body.message,
        respond_by=utcnow() + timedelta(hours=settings.request_response_hours),
    )
    db.add(req)
    db.commit()
    guide_user = db.get(User, g.user_id)
    text = f"New request: {body.date_from}..{body.date_to}, group of {body.group_size}."
    notifier.send_email(guide_user.email, "New booking request", text)
    if guide_user.telegram_chat_id:
        notifier.send_telegram(guide_user.telegram_chat_id, text)
    return req


@router.get("/requests/incoming", response_model=list[RequestOut])
def incoming(user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = db.scalar(select(GuideProfile).where(GuideProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(404, "guide_profile_required")
    rows = db.scalars(
        select(BookingRequest)
        .where(BookingRequest.guide_id == profile.id)
        .order_by(BookingRequest.created_at.desc())
    ).all()
    _expire_overdue(db, rows)
    db.commit()
    return rows


@router.get("/requests/mine", response_model=list[RequestOut])
def mine(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(BookingRequest)
        .where(BookingRequest.tourist_id == user.id)
        .order_by(BookingRequest.created_at.desc())
    ).all()
    _expire_overdue(db, rows)
    db.commit()
    return rows


@router.patch("/requests/{request_id}", response_model=RequestOut)
def decide(
    request_id: UUID,
    body: RequestDecision,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    req = db.get(BookingRequest, request_id)
    if req is None:
        raise HTTPException(404, "request_not_found")
    profile = db.get(GuideProfile, req.guide_id)
    if profile.user_id != user.id:
        raise HTTPException(403, "forbidden")
    if body.status not in (RequestStatus.accepted, RequestStatus.declined):
        raise HTTPException(422, "invalid_status")
    _expire_overdue(db, [req])
    if req.status != RequestStatus.pending:
        raise HTTPException(409, f"request_{req.status.value}")
    req.status = body.status
    db.commit()
    tourist = db.get(User, req.tourist_id)
    notifier.send_email(
        tourist.email, "Booking request update", f"Your request was {body.status.value}."
    )
    return req


@router.get("/files/documents/{doc_id}")
def get_signed_document(
    doc_id: UUID,
    expires: int | None = None,
    sig: str | None = None,
    db: Session = Depends(get_db),
):
    """AC-09: Guide documents are strictly inaccessible without a valid HMAC-signed link."""
    from app.core.security import verify_resource_signature

    if expires is None or not sig or not verify_resource_signature(str(doc_id), expires, sig):
        raise HTTPException(403, "invalid_or_expired_signature")
    doc = db.get(GuideDocument, doc_id)
    if doc is None:
        raise HTTPException(404, "document_not_found")
    return {"id": str(doc.id), "kind": doc.kind, "storage_key": doc.storage_key}

