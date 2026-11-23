"""Contacts / recipients routes."""
import csv
import io
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.contact import Contact
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse, ContactImportResult
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    request: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check for duplicate email within user scope
    existing = await db.execute(
        select(Contact).where(
            Contact.user_id == current_user.id,
            Contact.email == str(request.email),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Contact with this email already exists")

    contact = Contact(
        user_id=current_user.id,
        name=request.name,
        email=str(request.email),
        organization=request.organization,
        group_name=request.group_name,
    )
    db.add(contact)
    await db.flush()
    return ContactResponse.model_validate(contact)


@router.get("", response_model=PaginatedResponse[ContactResponse])
async def list_contacts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Contact).where(Contact.user_id == current_user.id)

    if search:
        query = query.where(
            (Contact.name.ilike(f"%{search}%")) | (Contact.email.ilike(f"%{search}%"))
        )
    if group:
        query = query.where(Contact.group_name == group)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(Contact.name).offset(offset).limit(per_page)
    )
    contacts = result.scalars().all()

    return PaginatedResponse(
        items=[ContactResponse.model_validate(c) for c in contacts],
        total=total,
        page=page,
        per_page=per_page,
        pages=max(1, (total + per_page - 1) // per_page),
    )


@router.get("/export")
async def export_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Contact).where(Contact.user_id == current_user.id).order_by(Contact.name)
    )
    contacts = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "email", "organization", "group"])
    for c in contacts:
        writer.writerow([c.name, c.email, c.organization or "", c.group_name or ""])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts.csv"},
    )


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = await _get_owned_contact(db, contact_id, current_user.id)
    return ContactResponse.model_validate(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: uuid.UUID,
    request: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = await _get_owned_contact(db, contact_id, current_user.id)

    if request.name is not None:
        contact.name = request.name
    if request.email is not None:
        contact.email = str(request.email)
    if request.organization is not None:
        contact.organization = request.organization
    if request.group_name is not None:
        contact.group_name = request.group_name

    await db.flush()
    return ContactResponse.model_validate(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = await _get_owned_contact(db, contact_id, current_user.id)
    await db.delete(contact)


@router.post("/import", response_model=ContactImportResult)
async def import_contacts(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        name = (row.get("name") or "").strip()
        email = (row.get("email") or "").strip()

        if not email:
            errors.append(f"Row {i}: missing email")
            skipped += 1
            continue

        # Check for duplicate
        existing = await db.execute(
            select(Contact).where(
                Contact.user_id == current_user.id,
                Contact.email == email,
            )
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        contact = Contact(
            user_id=current_user.id,
            name=name or email,
            email=email,
            organization=(row.get("organization") or "").strip() or None,
            group_name=(row.get("group") or "").strip() or None,
        )
        db.add(contact)
        imported += 1

    await db.flush()
    return ContactImportResult(imported=imported, skipped=skipped, errors=errors[:20])


async def _get_owned_contact(
    db: AsyncSession, contact_id: uuid.UUID, user_id: uuid.UUID
) -> Contact:
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.user_id == user_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact
