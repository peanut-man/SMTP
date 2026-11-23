"""SQLAlchemy model for SMTP accounts."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, Integer, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class SecurityMode(str, enum.Enum):
    STARTTLS = "STARTTLS"
    SSL_TLS = "SSL_TLS"
    PLAIN = "PLAIN"


class TestStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    UNTESTED = "untested"


class SMTPAccount(Base):
    __tablename__ = "smtp_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_name: Mapped[str] = mapped_column(String(128), nullable=False)
    smtp_host: Mapped[str] = mapped_column(String(255), nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    security_mode: Mapped[SecurityMode] = mapped_column(
        SAEnum(SecurityMode, name="security_mode"), default=SecurityMode.STARTTLS, nullable=False
    )
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    connection_timeout: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_status: Mapped[TestStatus] = mapped_column(
        SAEnum(TestStatus, name="test_status"), default=TestStatus.UNTESTED, nullable=False
    )
    last_test_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="smtp_accounts")
    email_jobs: Mapped[list["EmailJob"]] = relationship("EmailJob", back_populates="smtp_account")
    email_attempts: Mapped[list["EmailAttempt"]] = relationship(
        "EmailAttempt", back_populates="smtp_account"
    )

    def __repr__(self) -> str:
        return f"<SMTPAccount id={self.id} name={self.account_name} host={self.smtp_host}>"
