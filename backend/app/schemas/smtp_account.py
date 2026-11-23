"""SMTP account Pydantic schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import uuid
from datetime import datetime


class SMTPAccountCreate(BaseModel):
    account_name: str
    smtp_host: str
    smtp_port: int
    username: str
    password: str
    security_mode: str = "STARTTLS"
    sender_email: EmailStr
    sender_name: str = ""
    connection_timeout: int = 30
    is_default: bool = False

    @field_validator("smtp_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("security_mode")
    @classmethod
    def validate_security_mode(cls, v: str) -> str:
        allowed = {"STARTTLS", "SSL_TLS", "PLAIN"}
        if v not in allowed:
            raise ValueError(f"security_mode must be one of {allowed}")
        return v

    @field_validator("connection_timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if not (5 <= v <= 120):
            raise ValueError("Timeout must be between 5 and 120 seconds")
        return v


class SMTPAccountUpdate(BaseModel):
    account_name: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None  # None means don't update password
    security_mode: Optional[str] = None
    sender_email: Optional[EmailStr] = None
    sender_name: Optional[str] = None
    connection_timeout: Optional[int] = None
    is_active: Optional[bool] = None


class SMTPAccountResponse(BaseModel):
    id: uuid.UUID
    account_name: str
    smtp_host: str
    smtp_port: int
    username: str
    security_mode: str
    sender_email: str
    sender_name: str
    connection_timeout: int
    is_default: bool
    is_active: bool
    last_tested_at: Optional[datetime]
    last_test_status: str
    last_test_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SMTPTestResult(BaseModel):
    success: bool
    message: str
    details: Optional[str] = None
    tested_at: datetime
