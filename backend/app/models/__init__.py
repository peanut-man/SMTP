"""Package init — import all models so Alembic can discover them."""
from app.models.user import User, UserRole
from app.models.smtp_account import SMTPAccount, SecurityMode, TestStatus
from app.models.email_job import EmailJob, JobStatus, MessageType
from app.models.email_recipient import EmailRecipient, RecipientType, RecipientStatus
from app.models.email_template import EmailTemplate
from app.models.email_attempt import EmailAttempt, AttemptStatus
from app.models.contact import Contact

__all__ = [
    "User",
    "UserRole",
    "SMTPAccount",
    "SecurityMode",
    "TestStatus",
    "EmailJob",
    "JobStatus",
    "MessageType",
    "EmailRecipient",
    "RecipientType",
    "RecipientStatus",
    "EmailTemplate",
    "EmailAttempt",
    "AttemptStatus",
    "Contact",
]
