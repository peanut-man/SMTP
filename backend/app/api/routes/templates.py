"""Email templates routes."""
import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.email_template import EmailTemplate
from app.models.user import User
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)
from app.services.template_service import render_template, extract_template_variables, validate_template_syntax
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    request: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate syntax
    for content in [request.html_content, request.text_content, request.subject]:
        if content:
            err = validate_template_syntax(content)
            if err:
                raise HTTPException(status_code=422, detail=f"Template syntax error: {err}")

    # Extract variables from all content fields
    variables = set()
    for content in [request.html_content, request.text_content, request.subject]:
        if content:
            variables.update(extract_template_variables(content))

    if request.variables:
        variables.update(request.variables)

    template = EmailTemplate(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        subject=request.subject,
        html_content=request.html_content,
        text_content=request.text_content,
        variables=sorted(variables),
    )
    db.add(template)
    await db.flush()
    return TemplateResponse.model_validate(template)


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EmailTemplate)
        .where(EmailTemplate.user_id == current_user.id)
        .order_by(EmailTemplate.updated_at.desc())
    )
    return [TemplateResponse.model_validate(t) for t in result.scalars().all()]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = await _get_owned_template(db, template_id, current_user.id)
    return TemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    request: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = await _get_owned_template(db, template_id, current_user.id)

    if request.name is not None:
        template.name = request.name
    if request.description is not None:
        template.description = request.description
    if request.subject is not None:
        template.subject = request.subject
    if request.html_content is not None:
        template.html_content = request.html_content
    if request.text_content is not None:
        template.text_content = request.text_content

    # Re-extract variables
    variables = set()
    for content in [template.html_content, template.text_content, template.subject]:
        if content:
            variables.update(extract_template_variables(content))
    if request.variables:
        variables.update(request.variables)
    template.variables = sorted(variables)

    await db.flush()
    return TemplateResponse.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = await _get_owned_template(db, template_id, current_user.id)
    await db.delete(template)


@router.post("/{template_id}/preview", response_model=TemplatePreviewResponse)
async def preview_template(
    template_id: uuid.UUID,
    request: TemplatePreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = await _get_owned_template(db, template_id, current_user.id)
    try:
        rendered = render_template(template, request.variables)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return TemplatePreviewResponse(
        subject=rendered.get("subject", ""),
        html_content=rendered.get("html_content"),
        text_content=rendered.get("text_content"),
    )


async def _get_owned_template(
    db: AsyncSession, template_id: uuid.UUID, user_id: uuid.UUID
) -> EmailTemplate:
    result = await db.execute(
        select(EmailTemplate).where(
            EmailTemplate.id == template_id,
            EmailTemplate.user_id == user_id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template
