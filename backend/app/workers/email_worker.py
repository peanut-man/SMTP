"""Background email worker — polls for PENDING jobs and processes them."""
import asyncio
import logging
import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.encryption import decrypt_password
from app.core.logging import setup_logging
from app.models.email_job import EmailJob, JobStatus
from app.models.email_recipient import EmailRecipient
from app.models.email_attempt import EmailAttempt, AttemptStatus
from app.models.smtp_account import SMTPAccount
from app.services.smtp_service import send_email_via_smtp, is_permanent_failure
from app.services.email_service import build_mime_message, get_all_recipient_addresses

setup_logging()
logger = logging.getLogger("email_worker")

POLL_INTERVAL = settings.WORKER_POLL_INTERVAL
MAX_CONCURRENT = settings.WORKER_MAX_CONCURRENT


def _compute_next_retry(retry_count: int) -> datetime:
    """Exponential backoff: base_delay * 2^retry_count seconds."""
    delay = settings.RETRY_BASE_DELAY * (2 ** retry_count)
    delay = min(delay, 3600)  # cap at 1 hour
    return datetime.now(timezone.utc) + timedelta(seconds=delay)


async def process_job(db: AsyncSession, job_id) -> None:
    """
    Process a single email job atomically.
    Uses SELECT FOR UPDATE SKIP LOCKED to prevent duplicate processing.
    """
    # Re-fetch with row-level lock
    result = await db.execute(
        select(EmailJob)
        .where(EmailJob.id == job_id)
        .with_for_update(skip_locked=True)
    )
    job = result.scalar_one_or_none()

    if job is None:
        # Another worker grabbed it
        return

    if job.status not in (JobStatus.PENDING, JobStatus.RETRYING):
        return

    # Mark as PROCESSING
    job.status = JobStatus.PROCESSING
    job.started_at = datetime.now(timezone.utc)
    await db.flush()

    # Load SMTP account
    smtp_result = await db.execute(
        select(SMTPAccount).where(SMTPAccount.id == job.smtp_account_id)
    )
    smtp_account = smtp_result.scalar_one_or_none()

    if smtp_account is None or not smtp_account.is_active:
        job.status = JobStatus.FAILED
        job.last_error = "SMTP account not found or inactive"
        job.completed_at = datetime.now(timezone.utc)
        await db.flush()
        return

    # Decrypt SMTP password
    try:
        decrypted_password = decrypt_password(smtp_account.encrypted_password)
    except ValueError:
        job.status = JobStatus.FAILED
        job.last_error = "Failed to decrypt SMTP credentials"
        job.completed_at = datetime.now(timezone.utc)
        await db.flush()
        return

    # Load recipients
    recipient_result = await db.execute(
        select(EmailRecipient).where(EmailRecipient.email_job_id == job.id)
    )
    recipients = list(recipient_result.scalars().all())

    # Build MIME message
    mime_message = build_mime_message(job, recipients)

    # Attempt to send
    attempt_number = job.retry_count + 1
    attempted_at = datetime.now(timezone.utc)

    success, smtp_code, smtp_message = await send_email_via_smtp(
        smtp_account, decrypted_password, mime_message
    )

    completed_at = datetime.now(timezone.utc)

    # Record the attempt
    attempt = EmailAttempt(
        email_job_id=job.id,
        smtp_account_id=smtp_account.id,
        attempt_number=attempt_number,
        status=AttemptStatus.SUCCESS if success else AttemptStatus.FAILED,
        smtp_response_code=smtp_code,
        smtp_response_message=smtp_message if success else None,
        error_message=None if success else smtp_message,
        attempted_at=attempted_at,
        completed_at=completed_at,
    )
    db.add(attempt)

    if success:
        job.status = JobStatus.ACCEPTED
        job.completed_at = completed_at
        job.last_error = None
        logger.info("Job %s accepted by SMTP server on attempt %d", job.id, attempt_number)
    else:
        job.retry_count += 1
        job.last_error = smtp_message

        # Check if permanent failure or retry limit reached
        permanent = is_permanent_failure(smtp_code)
        exhausted = job.retry_count >= job.max_retries

        if permanent or exhausted:
            job.status = JobStatus.FAILED
            job.completed_at = completed_at
            logger.warning(
                "Job %s permanently failed after %d attempt(s): %s",
                job.id, attempt_number, smtp_message
            )
        else:
            job.status = JobStatus.RETRYING
            job.next_retry_at = _compute_next_retry(job.retry_count)
            logger.info(
                "Job %s will retry (attempt %d/%d) at %s",
                job.id, job.retry_count, job.max_retries, job.next_retry_at
            )

    await db.flush()


async def poll_and_process(engine) -> None:
    """
    Poll for jobs eligible for processing and dispatch them.
    Uses SKIP LOCKED for safe concurrent workers.
    """
    AsyncSession = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    async with AsyncSession() as db:
        # Find eligible jobs: PENDING or RETRYING with next_retry_at in the past
        result = await db.execute(
            select(EmailJob.id)
            .where(
                (
                    (EmailJob.status == JobStatus.PENDING)
                    | (
                        (EmailJob.status == JobStatus.RETRYING)
                        & (EmailJob.next_retry_at <= now)
                    )
                )
            )
            .limit(MAX_CONCURRENT)
        )
        job_ids = [row[0] for row in result.fetchall()]

    if not job_ids:
        return

    logger.debug("Found %d job(s) to process", len(job_ids))

    # Process each job in its own transaction
    tasks = []
    for job_id in job_ids:
        AsyncSessionForJob = async_sessionmaker(engine, expire_on_commit=False)
        tasks.append(_process_job_in_transaction(AsyncSessionForJob, job_id))

    await asyncio.gather(*tasks, return_exceptions=True)


async def _process_job_in_transaction(session_maker, job_id) -> None:
    async with session_maker() as db:
        try:
            await process_job(db, job_id)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error("Error processing job %s: %s", job_id, str(e))


async def run_worker() -> None:
    """Main worker loop."""
    logger.info("Email worker starting. Poll interval: %ds", POLL_INTERVAL)

    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        echo=False,
    )

    while True:
        try:
            await poll_and_process(engine)
        except Exception as e:
            logger.error("Worker poll error: %s", str(e))

        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(run_worker())
