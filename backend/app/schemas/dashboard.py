"""Dashboard Pydantic schemas."""
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class DashboardSummary(BaseModel):
    total_emails: int
    accepted_emails: int
    failed_emails: int
    pending_emails: int
    retrying_emails: int
    cancelled_emails: int
    active_smtp_accounts: int
    total_smtp_accounts: int
    total_contacts: int
    total_templates: int


class EmailTrendPoint(BaseModel):
    date: str
    submitted: int
    accepted: int
    failed: int


class AccountPerformance(BaseModel):
    account_id: str
    account_name: str
    smtp_host: str
    total_sent: int
    accepted: int
    failed: int
    success_rate: float


class DashboardTrends(BaseModel):
    trends: List[EmailTrendPoint]


class DashboardAccountPerformance(BaseModel):
    accounts: List[AccountPerformance]
