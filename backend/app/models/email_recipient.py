"""SQLAlchemy model for email recipients."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class RecipientType(str, enum.Enum):
    TO = "to"
    CC = "cc"
    BCC = "bcc"


class RecipientStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    FAILED = "FAILED"


class EmailRecipient(Base):
    __tablename__ = "email_recipients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recipient_type: Mapped[RecipientType] = mapped_column(
        SAEnum(RecipientType, name="recipient_type"), default=RecipientType.TO, nullable=False
    )
    status: Mapped[RecipientStatus] = mapped_column(
        SAEnum(RecipientStatus, name="recipient_status"),
        default=RecipientStatus.PENDING,
        nullable=False,
    )
    smtp_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    email_job: Mapped["EmailJob"] = relationship("EmailJob", back_populates="recipients")

    def __repr__(self) -> str:
        return f"<EmailRecipient email={self.recipient_email} type={self.recipient_type}>"
