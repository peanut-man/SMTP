"""Fernet symmetric encryption for SMTP credentials."""
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

logger = logging.getLogger(__name__)

_dev_fallback_key: Optional[bytes] = None


def _get_fernet() -> Fernet:
    global _dev_fallback_key
    key = settings.ENCRYPTION_KEY
    if not key:
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(
                "ENCRYPTION_KEY is not set. Set it in .env or environment variables."
            )
        # In non-production, provide a stable session key and warn
        if _dev_fallback_key is None:
            logger.warning(
                "ENCRYPTION_KEY not set. Using auto-generated development encryption key."
            )
            _dev_fallback_key = Fernet.generate_key()
        return Fernet(_dev_fallback_key)

    # Accept raw 32-byte keys and auto-encode to base64 URL-safe format
    key_bytes = key.encode() if isinstance(key, str) else key
    if len(key_bytes) == 32:
        key_bytes = base64.urlsafe_b64encode(key_bytes)
    return Fernet(key_bytes)


def encrypt_password(plaintext: str) -> str:
    """Encrypt an SMTP password for database storage."""
    fernet = _get_fernet()
    encrypted = fernet.encrypt(plaintext.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_password(ciphertext: str) -> str:
    """Decrypt a stored SMTP password for use in SMTP operations."""
    fernet = _get_fernet()
    try:
        decrypted = fernet.decrypt(ciphertext.encode("utf-8"))
        return decrypted.decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt SMTP credential: invalid token") from exc


def generate_encryption_key() -> str:
    """Generate a new Fernet-compatible encryption key."""
    return Fernet.generate_key().decode("utf-8")
