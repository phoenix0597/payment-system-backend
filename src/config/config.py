from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    SECRET_KEY: str = ""
    WEBHOOK_SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_PREFIX: str = "/api/v1"
    TOKEN_URL: str = "/auth/token"

    model_config = SettingsConfigDict(
        env_file=[BASE_DIR / ".env.sample", BASE_DIR / ".env"],
        env_file_encoding="utf-8",
    )


settings = Settings()
