"""Dashboard routes."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, DashboardTrends, DashboardAccountPerformance
from app.services.analytics_service import get_dashboard_summary, get_email_trends, get_account_performance
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_dashboard_summary(db, current_user.id)


@router.get("/email-trends", response_model=DashboardTrends)
async def email_trends(
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trends = await get_email_trends(db, current_user.id, days=days)
    return DashboardTrends(trends=trends)


@router.get("/account-performance", response_model=DashboardAccountPerformance)
async def account_performance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accounts = await get_account_performance(db, current_user.id)
    return DashboardAccountPerformance(accounts=accounts)
