"""Application configuration loaded from environment variables / .env file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


class Settings(BaseSettings):
    """Runtime settings.

    Every value can be overridden through an environment variable with the same
    (case-insensitive) name, which keeps container/orchestrator deployments easy.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Broadcast Information"
    app_host: str = "localhost"
    app_port: int = 8000
    public_base_url: str = "http://localhost:8000"
    debug: bool = False

    database_url: str = f"sqlite:///{(BASE_DIR / 'database' / 'broadcast_db.sqlite').as_posix()}"

    # Authentication
    secret_key: str = "insecure-development-key-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7
    session_secret_key: str = "insecure-session-key-change-me"
    session_max_age_seconds: int = 60 * 60 * 8
    session_cookie_name: str = "broadcast_session"
    cookie_https_only: bool = False

    # Uploads
    storage_dir: Path = BASE_DIR / "storage" / "documents"
    max_upload_mb: int = 20

    # Mail
    smtp_sender_email: str = ""
    smtp_sender_password: str = ""
    smtp_timeout_seconds: int = 20
    sharp_smtp_host: str = "relay.sharp.co.jp"
    sharp_smtp_port: int = 25
    sharp_smtp_starttls: bool = True
    office_smtp_host: str = "smtp.office365.com"
    office_smtp_port: int = 587
    office_smtp_starttls: bool = True

    # UI
    default_page_size: int = 10
    max_page_size: int = 100

    @field_validator("storage_dir")
    @classmethod
    def _resolve_storage_dir(cls, value: Path) -> Path:
        return value if value.is_absolute() else (BASE_DIR / value).resolve()

    @field_validator("database_url")
    @classmethod
    def _resolve_sqlite_path(cls, value: str) -> str:
        prefix = "sqlite:///"
        if not value.startswith(prefix):
            return value
        raw_path = value[len(prefix):]
        path = Path(raw_path)
        if path.is_absolute():
            return value
        return f"{prefix}{(BASE_DIR / path).resolve().as_posix()}"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
