from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"
    database_url: str = "postgresql+psycopg://audioguide:audioguide@localhost:5433/audioguide"
    redis_url: str = "redis://localhost:6379/0"

    supported_langs: list[str] = ["kaa", "uz", "ru", "en"]
    default_lang: str = "en"

    # Auth
    jwt_secret: str = "dev-only-secret-change-me-in-production-0123456789"
    access_ttl_min: int = 15
    refresh_ttl_days: int = 30
    cookie_secure: bool = False
    otp_ttl_min: int = 10
    otp_max_attempts: int = 5

    # AI
    ai_limit_anonymous: int = 10
    ai_limit_registered: int = 30
    ai_daily_budget_usd: float = 10.0
    rag_threshold: float = 0.15
    rag_top_k: int = 4

    # Offline bundles
    bundle_max_bytes: int = 150 * 1024 * 1024

    # Guide requests
    request_response_hours: int = 24


settings = Settings()
