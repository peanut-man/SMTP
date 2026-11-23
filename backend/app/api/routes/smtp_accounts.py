"""SMTP accounts routes."""
import logging
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.core.encryption import encrypt_password, decrypt_password
from app.models.smtp_account import SMTPAccount, TestStatus
from app.models.user import User
from app.schemas.smtp_account import (
    SMTPAccountCreate,
    SMTPAccountUpdate,
    SMTPAccountResponse,
    SMTPTestResult,
)
from app.services.smtp_service import test_smtp_connection
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=SMTPAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_smtp_account(
    request: SMTPAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    encrypted = encrypt_password(request.password)

    # If this is to be default, clear existing default
    if request.is_default:
        await db.execute(
            update(SMTPAccount)
            .where(SMTPAccount.user_id == current_user.id)
            .values(is_default=False)
        )

    account = SMTPAccount(
        user_id=current_user.id,
        account_name=request.account_name,
        smtp_host=request.smtp_host,
        smtp_port=request.smtp_port,
        username=request.username,
        encrypted_password=encrypted,
        security_mode=request.security_mode,
        sender_email=str(request.sender_email),
        sender_name=request.sender_name,
        connection_timeout=request.connection_timeout,
        is_default=request.is_default,
    )
    db.add(account)
    await db.flush()
    return SMTPAccountResponse.model_validate(account)


@router.get("", response_model=List[SMTPAccountResponse])
async def list_smtp_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SMTPAccount)
        .where(SMTPAccount.user_id == current_user.id)
        .order_by(SMTPAccount.created_at.desc())
    )
    accounts = result.scalars().all()
    return [SMTPAccountResponse.model_validate(a) for a in accounts]


@router.get("/{account_id}", response_model=SMTPAccountResponse)
async def get_smtp_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_owned_account(db, account_id, current_user.id)
    return SMTPAccountResponse.model_validate(account)


@router.put("/{account_id}", response_model=SMTPAccountResponse)
async def update_smtp_account(
    account_id: uuid.UUID,
    request: SMTPAccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_owned_account(db, account_id, current_user.id)

    if request.account_name is not None:
        account.account_name = request.account_name
    if request.smtp_host is not None:
        account.smtp_host = request.smtp_host
    if request.smtp_port is not None:
        account.smtp_port = request.smtp_port
    if request.username is not None:
        account.username = request.username
    if request.password is not None:
        account.encrypted_password = encrypt_password(request.password)
    if request.security_mode is not None:
        account.security_mode = request.security_mode
    if request.sender_email is not None:
        account.sender_email = str(request.sender_email)
    if request.sender_name is not None:
        account.sender_name = request.sender_name
    if request.connection_timeout is not None:
        account.connection_timeout = request.connection_timeout
    if request.is_active is not None:
        account.is_active = request.is_active

    await db.flush()
    return SMTPAccountResponse.model_validate(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_smtp_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_owned_account(db, account_id, current_user.id)
    await db.delete(account)


@router.post("/{account_id}/test", response_model=SMTPTestResult)
async def test_smtp_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_owned_account(db, account_id, current_user.id)

    try:
        decrypted = decrypt_password(account.encrypted_password)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not decrypt stored SMTP credentials",
        )

    success, message, details = await test_smtp_connection(account, decrypted)

    # Update test results on the account record
    account.last_tested_at = datetime.now(timezone.utc)
    account.last_test_status = TestStatus.SUCCESS if success else TestStatus.FAILED
    account.last_test_error = details if not success else None
    await db.flush()

    return SMTPTestResult(
        success=success,
        message=message,
        details=details if not success else None,
        tested_at=account.last_tested_at,
    )


@router.post("/{account_id}/set-default", response_model=SMTPAccountResponse)
async def set_default_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_owned_account(db, account_id, current_user.id)

    # Clear existing default
    await db.execute(
        update(SMTPAccount)
        .where(SMTPAccount.user_id == current_user.id)
        .values(is_default=False)
    )
    account.is_default = True
    await db.flush()
    return SMTPAccountResponse.model_validate(account)


async def _get_owned_account(
    db: AsyncSession, account_id: uuid.UUID, user_id: uuid.UUID
) -> SMTPAccount:
    result = await db.execute(
        select(SMTPAccount).where(
            SMTPAccount.id == account_id,
            SMTPAccount.user_id == user_id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SMTP account not found",
        )
    return account
