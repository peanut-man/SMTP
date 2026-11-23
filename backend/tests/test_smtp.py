"""Tests for SMTP account management and credential encryption."""
import pytest
from httpx import AsyncClient
from app.core.encryption import encrypt_password, decrypt_password


# ── Encryption Tests ──────────────────────────────────────────────────────────

def test_encrypt_decrypt_roundtrip():
    original = "my_smtp_password"
    encrypted = encrypt_password(original)
    assert encrypted != original
    assert decrypt_password(encrypted) == original


def test_encrypt_produces_unique_ciphertexts():
    pw = "same_password"
    c1 = encrypt_password(pw)
    c2 = encrypt_password(pw)
    # Fernet uses a random IV so the same plaintext produces different ciphertexts
    assert c1 != c2


def test_decrypt_invalid_token():
    with pytest.raises(ValueError):
        decrypt_password("not-a-valid-fernet-token")


# ── SMTP Account API Tests ─────────────────────────────────────────────────────

SMTP_PAYLOAD = {
    "account_name": "Test Gmail",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "test@gmail.com",
    "password": "apppassword123",
    "security_mode": "STARTTLS",
    "sender_email": "test@gmail.com",
    "sender_name": "Test User",
    "connection_timeout": 30,
    "is_default": False,
}


@pytest.mark.asyncio
async def test_create_smtp_account(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/smtp-accounts", json=SMTP_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["account_name"] == "Test Gmail"
    assert "password" not in data  # Password never returned
    assert "encrypted_password" not in data


@pytest.mark.asyncio
async def test_list_smtp_accounts(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/smtp-accounts", json=SMTP_PAYLOAD, headers=auth_headers)
    resp = await client.get("/api/v1/smtp-accounts", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_smtp_account(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/smtp-accounts", json=SMTP_PAYLOAD, headers=auth_headers)
    account_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/smtp-accounts/{account_id}", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_smtp_account(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/smtp-accounts", json=SMTP_PAYLOAD, headers=auth_headers)
    account_id = create_resp.json()["id"]
    resp = await client.put(f"/api/v1/smtp-accounts/{account_id}",
        json={"account_name": "Updated Name"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["account_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_smtp_account(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/smtp-accounts", json=SMTP_PAYLOAD, headers=auth_headers)
    account_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/smtp-accounts/{account_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_cannot_access_other_users_account(client: AsyncClient, auth_headers: dict):
    # Create account with first user
    create_resp = await client.post("/api/v1/smtp-accounts", json=SMTP_PAYLOAD, headers=auth_headers)
    account_id = create_resp.json()["id"]

    # Register second user
    await client.post("/api/v1/auth/register", json={
        "username": "otheruser", "email": "other@example.com", "password": "password123"
    })
    login_resp = await client.post("/api/v1/auth/login", json={"email": "other@example.com", "password": "password123"})
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Other user should get 404 for first user's account
    resp = await client.get(f"/api/v1/smtp-accounts/{account_id}", headers=other_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_smtp_port(client: AsyncClient, auth_headers: dict):
    payload = {**SMTP_PAYLOAD, "smtp_port": 99999}
    resp = await client.post("/api/v1/smtp-accounts", json=payload, headers=auth_headers)
    assert resp.status_code == 422
