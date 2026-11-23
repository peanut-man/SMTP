"""SQLAlchemy model for email sending attempts."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class AttemptStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class EmailAttempt(Base):
    __tablename__ = "email_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    smtp_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("smtp_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AttemptStatus] = mapped_column(
        SAEnum(AttemptStatus, name="attempt_status"), nullable=False
    )
    smtp_response_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    smtp_response_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    email_job: Mapped["EmailJob"] = relationship("EmailJob", back_populates="attempts")
    smtp_account: Mapped["SMTPAccount"] = relationship(
        "SMTPAccount", back_populates="email_attempts"
    )

    def __repr__(self) -> str:
        return f"<EmailAttempt job={self.email_job_id} attempt={self.attempt_number} status={self.status}>"
