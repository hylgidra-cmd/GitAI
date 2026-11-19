from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AIMessage, AIUsage
from app.models.types import utcnow
from app.services.settings_store import get_setting


def today() -> str:
    return utcnow().strftime("%Y-%m-%d")


def spent_today_usd(db: Session) -> float:
    start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total = db.scalar(
        select(func.coalesce(func.sum(AIMessage.cost_usd), 0.0)).where(
            AIMessage.created_at >= start, AIMessage.created_at < start + timedelta(days=1)
        )
    )
    return float(total or 0.0)


def check_and_consume(db: Session, subject: str, registered: bool) -> None:
    """Enforce kill switch, budget and per-subject daily limit. Raises 503/429."""
    if not get_setting(db, "ai_enabled"):
        raise HTTPException(503, "ai_disabled")
    budget = get_setting(db, "ai_daily_budget_usd") or settings.ai_daily_budget_usd
    if spent_today_usd(db) >= budget * 1.2:
        raise HTTPException(503, "ai_budget_exceeded")
    key = "ai_limit_registered" if registered else "ai_limit_anonymous"
    limit = get_setting(db, key) or getattr(settings, key)
    row = db.scalar(select(AIUsage).where(AIUsage.subject == subject, AIUsage.day == today()))
    if row is None:
        row = AIUsage(subject=subject, day=today(), count=0)
        db.add(row)
    if row.count >= limit:
        raise HTTPException(429, "ai_daily_limit")
    row.count += 1
    db.flush()
