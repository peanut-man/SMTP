"""Application configuration using Pydantic Settings."""
from typing import List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "SMTP Mail Management Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Encryption key for SMTP passwords (Fernet requires base64-encoded 32-byte key)
    ENCRYPTION_KEY: str = ""  # Must be set in production via env var

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://smtp_user:smtp_pass@localhost:5432/smtp_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]

    # File storage
    STORAGE_PATH: str = "/app/storage/attachments"
    MAX_ATTACHMENT_SIZE_MB: int = 25
    MAX_TOTAL_ATTACHMENTS_MB: int = 50

    # Email queue
    WORKER_POLL_INTERVAL: int = 5  # seconds
    WORKER_MAX_CONCURRENT: int = 5
    DEFAULT_MAX_RETRIES: int = 3
    RETRY_BASE_DELAY: int = 60  # seconds (exponential backoff base)

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()
