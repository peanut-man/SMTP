"""Queue service — helpers for job management."""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.email_job import EmailJob, JobStatus

logger = logging.getLogger(__name__)


async def cancel_job(db: AsyncSession, job_id: uuid.UUID, user_id: uuid.UUID) -> Optional[EmailJob]:
    """Cancel a PENDING or RETRYING job."""
    result = await db.execute(
        select(EmailJob).where(
            EmailJob.id == job_id,
            EmailJob.user_id == user_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        return None
    if job.status not in (JobStatus.PENDING, JobStatus.RETRYING):
        raise ValueError(f"Cannot cancel job in status '{job.status}'")

    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.now(timezone.utc)
    await db.flush()
    return job


async def retry_job(db: AsyncSession, job_id: uuid.UUID, user_id: uuid.UUID) -> Optional[EmailJob]:
    """Manually reset a FAILED job to PENDING for retry."""
    result = await db.execute(
        select(EmailJob).where(
            EmailJob.id == job_id,
            EmailJob.user_id == user_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        return None
    if job.status != JobStatus.FAILED:
        raise ValueError(f"Cannot retry job in status '{job.status}'")

    job.status = JobStatus.PENDING
    job.retry_count = 0
    job.next_retry_at = None
    job.last_error = None
    job.completed_at = None
    job.started_at = None
    await db.flush()
    return job
