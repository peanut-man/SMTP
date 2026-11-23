"""Email sending routes."""
import json
import logging
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.encryption import decrypt_password
from app.models.email_job import EmailJob, JobStatus
from app.models.smtp_account import SMTPAccount
from app.models.user import User
from app.schemas.email import SendEmailRequest, EmailJobResponse, EmailDetailResponse, RecipientItem
from app.services.email_service import create_email_job
from app.services.queue_service import cancel_job, retry_job
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_ATTACHMENT_BYTES = settings.MAX_ATTACHMENT_SIZE_MB * 1024 * 1024


@router.post("/send", response_model=EmailJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_email(
    smtp_account_id: str = Form(...),
    subject: str = Form(...),
    recipients_json: str = Form(...),
    html_body: Optional[str] = Form(None),
    text_body: Optional[str] = Form(None),
    reply_to: Optional[str] = Form(None),
    template_id: Optional[str] = Form(None),
    template_variables_json: Optional[str] = Form(None),
    attachments: List[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an email job for background sending."""

    # Parse recipients from JSON string
    try:
        recipients_data = json.loads(recipients_json)
        recipients = [RecipientItem(**r) for r in recipients_data]
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid recipients format: {e}")

    # Parse template variables
    template_variables = None
    if template_variables_json:
        try:
            template_variables = json.loads(template_variables_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="Invalid template_variables JSON")

    # Build request object
    request = SendEmailRequest(
        smtp_account_id=uuid.UUID(smtp_account_id),
        subject=subject,
        recipients=recipients,
        html_body=html_body,
        text_body=text_body,
        reply_to=reply_to,
        template_id=uuid.UUID(template_id) if template_id else None,
        template_variables=template_variables,
    )

    # Verify SMTP account ownership
    smtp_result = await db.execute(
        select(SMTPAccount).where(
            SMTPAccount.id == request.smtp_account_id,
            SMTPAccount.user_id == current_user.id,
            SMTPAccount.is_active == True,
        )
    )
    smtp_account = smtp_result.scalar_one_or_none()
    if not smtp_account:
        raise HTTPException(status_code=404, detail="SMTP account not found or inactive")

    # Save attachments
    attachment_paths = []
    for upload in attachments:
        if upload.filename:
            content = await upload.read()
            if len(content) > MAX_ATTACHMENT_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"Attachment '{upload.filename}' exceeds {settings.MAX_ATTACHMENT_SIZE_MB}MB limit",
                )
            safe_name = f"{uuid.uuid4()}_{upload.filename}"
            path = os.path.join(settings.STORAGE_PATH, safe_name)
            os.makedirs(settings.STORAGE_PATH, exist_ok=True)
            with open(path, "wb") as f:
                f.write(content)
            attachment_paths.append(path)

    # Create the job
    job = await create_email_job(
        db=db,
        user_id=current_user.id,
        request=request,
        smtp_account=smtp_account,
        attachment_paths=attachment_paths or None,
    )

    return EmailJobResponse.model_validate(job)


@router.get("/{email_id}", response_model=EmailDetailResponse)
async def get_email(
    email_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.email_recipient import EmailRecipient
    from app.models.email_attempt import EmailAttempt
    from app.schemas.email import EmailRecipientResponse, EmailAttemptResponse

    job = await _get_owned_job(db, email_id, current_user.id)

    recipients_result = await db.execute(
        select(EmailRecipient).where(EmailRecipient.email_job_id == email_id)
    )
    attempts_result = await db.execute(
        select(EmailAttempt)
        .where(EmailAttempt.email_job_id == email_id)
        .order_by(EmailAttempt.attempt_number)
    )

    return EmailDetailResponse(
        job=EmailJobResponse.model_validate(job),
        recipients=[EmailRecipientResponse.model_validate(r) for r in recipients_result.scalars().all()],
        attempts=[EmailAttemptResponse.model_validate(a) for a in attempts_result.scalars().all()],
    )


@router.post("/{email_id}/retry", response_model=EmailJobResponse)
async def retry_email(
    email_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await retry_job(db, email_id, current_user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Email job not found")
    return EmailJobResponse.model_validate(job)


@router.post("/{email_id}/cancel", response_model=EmailJobResponse)
async def cancel_email(
    email_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        job = await cancel_job(db, email_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not job:
        raise HTTPException(status_code=404, detail="Email job not found")
    return EmailJobResponse.model_validate(job)


async def _get_owned_job(db: AsyncSession, job_id: uuid.UUID, user_id: uuid.UUID) -> EmailJob:
    result = await db.execute(
        select(EmailJob).where(EmailJob.id == job_id, EmailJob.user_id == user_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Email job not found")
    return job
