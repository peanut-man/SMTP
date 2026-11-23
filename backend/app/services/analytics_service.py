"""Analytics service for dashboard data."""
import logging
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_job import EmailJob, JobStatus
from app.models.smtp_account import SMTPAccount
from app.models.email_template import EmailTemplate
from app.models.contact import Contact
from app.schemas.dashboard import (
    DashboardSummary,
    EmailTrendPoint,
    AccountPerformance,
)

logger = logging.getLogger(__name__)


async def get_dashboard_summary(db: AsyncSession, user_id) -> DashboardSummary:
    """Compute summary statistics for the dashboard."""

    # Email job counts by status
    job_stats = await db.execute(
        select(
            func.count(EmailJob.id).label("total"),
            func.sum(case((EmailJob.status == JobStatus.ACCEPTED, 1), else_=0)).label("accepted"),
            func.sum(case((EmailJob.status == JobStatus.FAILED, 1), else_=0)).label("failed"),
            func.sum(case((EmailJob.status == JobStatus.PENDING, 1), else_=0)).label("pending"),
            func.sum(case((EmailJob.status == JobStatus.RETRYING, 1), else_=0)).label("retrying"),
            func.sum(case((EmailJob.status == JobStatus.CANCELLED, 1), else_=0)).label("cancelled"),
        ).where(EmailJob.user_id == user_id)
    )
    row = job_stats.one()

    # SMTP account counts
    smtp_stats = await db.execute(
        select(
            func.count(SMTPAccount.id).label("total"),
            func.sum(case((SMTPAccount.is_active == True, 1), else_=0)).label("active"),
        ).where(SMTPAccount.user_id == user_id)
    )
    smtp_row = smtp_stats.one()

    # Contact count
    contact_count = await db.execute(
        select(func.count(Contact.id)).where(Contact.user_id == user_id)
    )
    total_contacts = contact_count.scalar() or 0

    # Template count
    template_count = await db.execute(
        select(func.count(EmailTemplate.id)).where(EmailTemplate.user_id == user_id)
    )
    total_templates = template_count.scalar() or 0

    return DashboardSummary(
        total_emails=row.total or 0,
        accepted_emails=row.accepted or 0,
        failed_emails=row.failed or 0,
        pending_emails=row.pending or 0,
        retrying_emails=row.retrying or 0,
        cancelled_emails=row.cancelled or 0,
        active_smtp_accounts=int(smtp_row.active or 0),
        total_smtp_accounts=smtp_row.total or 0,
        total_contacts=total_contacts,
        total_templates=total_templates,
    )


async def get_email_trends(
    db: AsyncSession,
    user_id,
    days: int = 30,
) -> List[EmailTrendPoint]:
    """Return daily email submission trends for the past N days."""
    from sqlalchemy import cast, Date

    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            cast(EmailJob.created_at, Date).label("date"),
            func.count(EmailJob.id).label("submitted"),
            func.sum(case((EmailJob.status == JobStatus.ACCEPTED, 1), else_=0)).label("accepted"),
            func.sum(case((EmailJob.status == JobStatus.FAILED, 1), else_=0)).label("failed"),
        )
        .where(EmailJob.user_id == user_id, EmailJob.created_at >= since)
        .group_by(cast(EmailJob.created_at, Date))
        .order_by(cast(EmailJob.created_at, Date))
    )

    return [
        EmailTrendPoint(
            date=str(row.date),
            submitted=row.submitted or 0,
            accepted=row.accepted or 0,
            failed=row.failed or 0,
        )
        for row in result
    ]


async def get_account_performance(
    db: AsyncSession,
    user_id,
) -> List[AccountPerformance]:
    """Return per-SMTP-account sending performance metrics."""
    result = await db.execute(
        select(
            SMTPAccount.id,
            SMTPAccount.account_name,
            SMTPAccount.smtp_host,
            func.count(EmailJob.id).label("total_sent"),
            func.sum(case((EmailJob.status == JobStatus.ACCEPTED, 1), else_=0)).label("accepted"),
            func.sum(case((EmailJob.status == JobStatus.FAILED, 1), else_=0)).label("failed"),
        )
        .join(EmailJob, EmailJob.smtp_account_id == SMTPAccount.id, isouter=True)
        .where(SMTPAccount.user_id == user_id)
        .group_by(SMTPAccount.id, SMTPAccount.account_name, SMTPAccount.smtp_host)
    )

    performances = []
    for row in result:
        total = row.total_sent or 0
        accepted = row.accepted or 0
        success_rate = (accepted / total * 100) if total > 0 else 0.0
        performances.append(
            AccountPerformance(
                account_id=str(row.id),
                account_name=row.account_name,
                smtp_host=row.smtp_host,
                total_sent=total,
                accepted=accepted,
                failed=row.failed or 0,
                success_rate=round(success_rate, 2),
            )
        )

    return performances
