"""Email Pydantic schemas."""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, EmailStr, field_validator
import uuid
from datetime import datetime


class RecipientItem(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    type: str = "to"  # to | cc | bcc

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in {"to", "cc", "bcc"}:
            raise ValueError("type must be 'to', 'cc', or 'bcc'")
        return v


class SendEmailRequest(BaseModel):
    smtp_account_id: uuid.UUID
    subject: str
    recipients: List[RecipientItem]
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    reply_to: Optional[EmailStr] = None
    template_id: Optional[uuid.UUID] = None
    template_variables: Optional[Dict[str, Any]] = None
    # Attachments are uploaded separately via multipart

    @field_validator("recipients")
    @classmethod
    def validate_recipients(cls, v: List[RecipientItem]) -> List[RecipientItem]:
        to_recipients = [r for r in v if r.type == "to"]
        if not to_recipients:
            raise ValueError("At least one 'to' recipient is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 recipients per email")
        return v

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Subject cannot be empty")
        if len(v) > 998:
            raise ValueError("Subject too long (max 998 characters)")
        return v


class EmailJobResponse(BaseModel):
    id: uuid.UUID
    subject: str
    sender_email: str
    sender_name: Optional[str]
    reply_to: Optional[str]
    recipient_count: int
    message_type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    last_error: Optional[str]
    retry_count: int
    max_retries: int
    next_retry_at: Optional[datetime]
    smtp_account_id: uuid.UUID

    model_config = {"from_attributes": True}


class EmailRecipientResponse(BaseModel):
    id: uuid.UUID
    recipient_email: str
    recipient_name: Optional[str]
    recipient_type: str
    status: str
    smtp_response: Optional[str]

    model_config = {"from_attributes": True}


class EmailAttemptResponse(BaseModel):
    id: uuid.UUID
    attempt_number: int
    status: str
    smtp_response_code: Optional[int]
    smtp_response_message: Optional[str]
    error_message: Optional[str]
    attempted_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class EmailDetailResponse(BaseModel):
    job: EmailJobResponse
    recipients: List[EmailRecipientResponse]
    attempts: List[EmailAttemptResponse]
