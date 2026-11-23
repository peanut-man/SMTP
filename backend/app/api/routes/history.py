"""Email history routes with filtering and pagination."""
import logging
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.core.database import get_db
from app.models.email_job import EmailJob, JobStatus
from app.models.smtp_account import SMTPAccount
from app.models.user import User
from app.schemas.email import EmailJobResponse
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=PaginatedResponse[EmailJobResponse])
async def get_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    smtp_account_id: Optional[uuid.UUID] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(EmailJob).where(EmailJob.user_id == current_user.id)

    if status:
        try:
            query = query.where(EmailJob.status == JobStatus(status))
        except ValueError:
            pass

    if smtp_account_id:
        query = query.where(EmailJob.smtp_account_id == smtp_account_id)

    if search:
        query = query.where(EmailJob.subject.ilike(f"%{search}%"))

    if date_from:
        query = query.where(EmailJob.created_at >= date_from)

    if date_to:
        query = query.where(EmailJob.created_at <= date_to)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    query = query.order_by(EmailJob.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return PaginatedResponse(
        items=[EmailJobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        per_page=per_page,
        pages=max(1, (total + per_page - 1) // per_page),
    )


@router.get("/{email_id}", response_model=EmailJobResponse)
async def get_history_item(
    email_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    result = await db.execute(
        select(EmailJob).where(
            EmailJob.id == email_id,
            EmailJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Email job not found")
    return EmailJobResponse.model_validate(job)


@router.get("/{email_id}/attempts")
async def get_attempts(
    email_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    from app.models.email_attempt import EmailAttempt
    from app.schemas.email import EmailAttemptResponse

    # Verify ownership
    job_result = await db.execute(
        select(EmailJob).where(
            EmailJob.id == email_id,
            EmailJob.user_id == current_user.id,
        )
    )
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Email job not found")

    result = await db.execute(
        select(EmailAttempt)
        .where(EmailAttempt.email_job_id == email_id)
        .order_by(EmailAttempt.attempt_number)
    )
    return [EmailAttemptResponse.model_validate(a) for a in result.scalars().all()]
