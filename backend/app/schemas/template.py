"""Template Pydantic schemas."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid
from datetime import datetime


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    variables: Optional[List[str]] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    variables: Optional[List[str]] = None


class TemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    subject: str
    html_content: Optional[str]
    text_content: Optional[str]
    variables: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TemplatePreviewRequest(BaseModel):
    variables: Dict[str, Any] = {}


class TemplatePreviewResponse(BaseModel):
    subject: str
    html_content: Optional[str]
    text_content: Optional[str]
