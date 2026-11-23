"""Email construction and job management service."""
import logging
import os
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.email_job import EmailJob, JobStatus, MessageType
from app.models.email_recipient import EmailRecipient, RecipientType
from app.models.smtp_account import SMTPAccount
from app.schemas.email import SendEmailRequest, RecipientItem
from app.services.template_service import render_template
from app.core.config import settings

logger = logging.getLogger(__name__)


async def create_email_job(
    db: AsyncSession,
    user_id: uuid.UUID,
    request: SendEmailRequest,
    smtp_account: SMTPAccount,
    attachment_paths: Optional[List[str]] = None,
) -> EmailJob:
    """Create a persistent email job and its recipient records."""

    # Resolve template if provided
    html_body = request.html_body
    text_body = request.text_body
    subject = request.subject
    msg_type = MessageType.DIRECT

    if request.template_id:
        from app.models.email_template import EmailTemplate
        tmpl_result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.id == request.template_id)
        )
        template = tmpl_result.scalar_one_or_none()
        if template:
            variables = request.template_variables or {}
            rendered = render_template(template, variables)
            html_body = rendered.get("html_content") or html_body
            text_body = rendered.get("text_content") or text_body
            subject = rendered.get("subject") or subject
            msg_type = MessageType.TEMPLATE

    attachments_meta = None
    if attachment_paths:
        attachments_meta = [
            {"path": p, "filename": os.path.basename(p)}
            for p in attachment_paths
        ]

    job = EmailJob(
        user_id=user_id,
        smtp_account_id=smtp_account.id,
        subject=subject,
        sender_email=smtp_account.sender_email,
        sender_name=smtp_account.sender_name,
        reply_to=str(request.reply_to) if request.reply_to else None,
        html_body=html_body,
        text_body=text_body,
        recipient_count=len(request.recipients),
        message_type=msg_type,
        template_id=request.template_id,
        attachments_meta=attachments_meta,
        status=JobStatus.PENDING,
        max_retries=settings.DEFAULT_MAX_RETRIES,
    )
    db.add(job)
    await db.flush()  # get job.id without committing

    # Create recipient records
    for recipient_data in request.recipients:
        recipient = EmailRecipient(
            email_job_id=job.id,
            recipient_email=str(recipient_data.email),
            recipient_name=recipient_data.name,
            recipient_type=RecipientType(recipient_data.type),
        )
        db.add(recipient)

    await db.flush()
    return job


def build_mime_message(
    job: EmailJob,
    recipients: List[EmailRecipient],
) -> MIMEMultipart:
    """
    Build a fully-constructed MIME email message ready for SMTP sending.
    """
    # Determine content structure
    has_html = bool(job.html_body)
    has_text = bool(job.text_body)
    has_attachments = bool(job.attachments_meta)

    if has_attachments:
        msg = MIMEMultipart("mixed")
        body_part = MIMEMultipart("alternative")
        if has_text:
            body_part.attach(MIMEText(job.text_body, "plain", "utf-8"))
        if has_html:
            body_part.attach(MIMEText(job.html_body, "html", "utf-8"))
        msg.attach(body_part)
    elif has_html and has_text:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(job.text_body, "plain", "utf-8"))
        msg.attach(MIMEText(job.html_body, "html", "utf-8"))
    elif has_html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(job.html_body, "html", "utf-8"))
    else:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(job.text_body or "", "plain", "utf-8"))

    # Headers
    sender = f"{job.sender_name} <{job.sender_email}>" if job.sender_name else job.sender_email
    msg["From"] = sender
    msg["Subject"] = job.subject

    if job.reply_to:
        msg["Reply-To"] = job.reply_to

    # Recipient headers
    to_list = [
        f"{r.recipient_name} <{r.recipient_email}>" if r.recipient_name else r.recipient_email
        for r in recipients if r.recipient_type == RecipientType.TO
    ]
    cc_list = [
        f"{r.recipient_name} <{r.recipient_email}>" if r.recipient_name else r.recipient_email
        for r in recipients if r.recipient_type == RecipientType.CC
    ]

    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)

    # Attachments
    if has_attachments and job.attachments_meta:
        for att in job.attachments_meta:
            filepath = att.get("path")
            filename = att.get("filename", os.path.basename(filepath))
            if filepath and os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                msg.attach(part)

    return msg


def get_all_recipient_addresses(recipients: List[EmailRecipient]) -> List[str]:
    """Return all recipient email addresses (TO + CC + BCC)."""
    return [r.recipient_email for r in recipients]
