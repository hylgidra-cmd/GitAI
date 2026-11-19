from sqlalchemy.orm import Session

from app.models import Setting

DEFAULTS = {
    "ai_enabled": True,
    "ai_limit_anonymous": None,  # None -> use config default
    "ai_limit_registered": None,
    "ai_daily_budget_usd": None,
    "commission_percent": 12,
    "kaa_tts_enabled": False,  # TZ section 6 & CM-03: kaa uses human narrators unless spike passes
    "voice_enabled_langs": ["uz", "ru", "en"],  # TZ AC-06: only langs >= 85% accuracy
}


def get_setting(db: Session, key: str, default=None):
    row = db.get(Setting, key)
    if row is None or "v" not in row.value:
        return DEFAULTS.get(key) if default is None else default
    return row.value["v"]


def set_setting(db: Session, key: str, value) -> None:
    row = db.get(Setting, key)
    if row is None:
        db.add(Setting(key=key, value={"v": value}))
    else:
        row.value = {"v": value}
    db.flush()
