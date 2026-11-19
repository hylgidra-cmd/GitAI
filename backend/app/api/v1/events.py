from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Event
from app.schemas.public import EventBatch

router = APIRouter(tags=["analytics"])

ALLOWED = {
    "qr_scan", "place_view", "audio_play", "audio_progress", "audio_complete",
    "offline_download_start", "offline_download_finish", "offline_download_fail",
    "ai_query", "ai_feedback", "guide_search", "request_sent", "request_answered",
}
FORBIDDEN_PROP_KEYS = {"email", "name", "phone", "lat", "lng", "ip"}


@router.post("/events", status_code=202)
def ingest(body: EventBatch, db: Session = Depends(get_db)):
    if len(body.events) > 100:
        raise HTTPException(413, "too_many_events")
    accepted = 0
    for e in body.events:
        if e.name not in ALLOWED:
            continue
        props = {k: v for k, v in e.props.items() if k not in FORBIDDEN_PROP_KEYS}
        db.add(Event(name=e.name, device_id=body.device_id, props=props))
        accepted += 1
    db.commit()
    return {"accepted": accepted}
