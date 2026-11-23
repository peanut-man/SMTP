"""Contact Pydantic schemas."""
from typing import Optional, List
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime


class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    organization: Optional[str] = None
    group_name: Optional[str] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    organization: Optional[str] = None
    group_name: Optional[str] = None


class ContactResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    organization: Optional[str]
    group_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactImportResult(BaseModel):
    imported: int
    skipped: int
    errors: List[str]
