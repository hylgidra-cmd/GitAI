from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://audioguide:audioguide@localhost:5432/audioguide"
    redis_url: str = "redis://localhost:6379/0"
    supported_langs: list[str] = ["kaa", "uz", "ru", "en"]
    default_lang: str = "en"


settings = Settings()
