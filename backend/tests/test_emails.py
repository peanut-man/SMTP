"""Tests for email sending, templates, and contacts."""
import pytest
from httpx import AsyncClient
from app.services.template_service import render_template, extract_template_variables, validate_template_syntax
from app.models.email_template import EmailTemplate


# ── Template Service Tests ────────────────────────────────────────────────────

def _make_template(subject="Hello {{ name }}", html="<b>{{ name }}</b>", text="Hello {{ name }}"):
    t = EmailTemplate.__new__(EmailTemplate)
    t.id = None
    t.subject = subject
    t.html_content = html
    t.text_content = text
    return t


def test_render_template_basic():
    tmpl = _make_template()
    result = render_template(tmpl, {"name": "Alice"})
    assert "Alice" in result["subject"]
    assert "Alice" in result["html_content"]


def test_render_template_missing_variable():
    tmpl = _make_template()
    with pytest.raises(ValueError):
        render_template(tmpl, {})  # name not provided → StrictUndefined raises


def test_extract_variables():
    content = "Hello {{ name }}, your code is {{ code }}."
    variables = extract_template_variables(content)
    assert "name" in variables
    assert "code" in variables


def test_validate_syntax_valid():
    result = validate_template_syntax("Hello {{ name }}")
    assert result is None


def test_validate_syntax_invalid():
    result = validate_template_syntax("Hello {% invalid %}")
    assert result is not None


# ── Template API Tests ─────────────────────────────────────────────────────────

TEMPLATE_PAYLOAD = {
    "name": "Welcome Email",
    "description": "Sent to new users",
    "subject": "Welcome {{ name }}!",
    "html_content": "<h1>Hello {{ name }}</h1>",
    "text_content": "Hello {{ name }}",
}


@pytest.mark.asyncio
async def test_create_template(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/templates", json=TEMPLATE_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Welcome Email"
    assert "name" in (data.get("variables") or [])


@pytest.mark.asyncio
async def test_list_templates(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/templates", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_preview_template(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/templates", json=TEMPLATE_PAYLOAD, headers=auth_headers)
    template_id = create_resp.json()["id"]
    resp = await client.post(f"/api/v1/templates/{template_id}/preview",
        json={"variables": {"name": "Bob"}}, headers=auth_headers)
    assert resp.status_code == 200
    assert "Bob" in resp.json()["subject"]


@pytest.mark.asyncio
async def test_delete_template(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/templates", json=TEMPLATE_PAYLOAD, headers=auth_headers)
    template_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/templates/{template_id}", headers=auth_headers)
    assert resp.status_code == 204


# ── Contact API Tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_contact(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/contacts", json={
        "name": "John Doe",
        "email": "john@example.com",
        "organization": "ACME",
        "group_name": "Newsletter",
    }, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["email"] == "john@example.com"


@pytest.mark.asyncio
async def test_duplicate_contact(client: AsyncClient, auth_headers: dict):
    payload = {"name": "Dup User", "email": "dupcontact@example.com"}
    await client.post("/api/v1/contacts", json=payload, headers=auth_headers)
    resp = await client.post("/api/v1/contacts", json=payload, headers=auth_headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_contacts(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/contacts", headers=auth_headers)
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.asyncio
async def test_search_contacts(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/contacts", json={"name": "Searchable User", "email": "searchable@example.com"}, headers=auth_headers)
    resp = await client.get("/api/v1/contacts?search=Searchable", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("ok", "degraded")
