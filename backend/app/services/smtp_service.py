"""SMTP connection service — testing and sending via aiosmtplib."""
import asyncio
import logging
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Optional, Tuple

import aiosmtplib

from app.core.config import settings
from app.models.smtp_account import SMTPAccount, SecurityMode

logger = logging.getLogger(__name__)

# SMTP response codes that indicate a permanent failure (no retry)
PERMANENT_FAILURE_CODES = {500, 501, 503, 530, 535, 550, 551, 552, 553, 554}
# Temporary failure codes (eligible for retry)
TEMPORARY_FAILURE_CODES = {421, 450, 451, 452}


def _build_ssl_context(validate_certs: bool = True) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if not validate_certs:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


async def test_smtp_connection(account: SMTPAccount, decrypted_password: str) -> Tuple[bool, str, Optional[str]]:
    """
    Test an SMTP connection.

    Returns:
        (success, message, details)
    """
    hostname = account.smtp_host
    port = account.smtp_port
    username = account.username
    timeout = account.connection_timeout
    mode = account.security_mode

    try:
        ssl_context = _build_ssl_context(validate_certs=True)

        if mode == SecurityMode.SSL_TLS:
            # Implicit TLS — connect with TLS from the start
            smtp = aiosmtplib.SMTP(
                hostname=hostname,
                port=port,
                use_tls=True,
                tls_context=ssl_context,
                timeout=timeout,
            )
            await smtp.connect()
        elif mode == SecurityMode.STARTTLS:
            # Connect plaintext, then upgrade via STARTTLS
            smtp = aiosmtplib.SMTP(
                hostname=hostname,
                port=port,
                use_tls=False,
                timeout=timeout,
            )
            await smtp.connect()
            await smtp.starttls(tls_context=ssl_context)
        else:
            # PLAIN (only for explicitly configured dev environments)
            smtp = aiosmtplib.SMTP(
                hostname=hostname,
                port=port,
                use_tls=False,
                timeout=timeout,
            )
            await smtp.connect()

        # Authenticate
        await smtp.login(username, decrypted_password)

        # Verify SMTP session is functional — NOOP command
        await smtp.noop()
        await smtp.quit()

        return True, "Connection successful. SMTP server accepted credentials.", None

    except aiosmtplib.SMTPAuthenticationError as e:
        return False, "Authentication failed. Check username and password.", f"SMTP code {e.code}"
    except aiosmtplib.SMTPConnectError as e:
        return False, "Connection refused. Check host and port.", str(e)
    except aiosmtplib.SMTPServerDisconnected as e:
        return False, "Server disconnected unexpectedly.", str(e)
    except ssl.SSLError as e:
        return False, "TLS handshake failed. Check security settings.", str(e)
    except asyncio.TimeoutError:
        return False, f"Connection timed out after {timeout}s.", None
    except OSError as e:
        if "Name or service not known" in str(e) or "getaddrinfo failed" in str(e):
            return False, f"DNS resolution failed for host '{hostname}'.", str(e)
        return False, "Network error connecting to SMTP server.", str(e)
    except Exception as e:
        logger.error("Unexpected SMTP test error for host %s: %s", hostname, type(e).__name__)
        return False, "Unexpected error during connection test.", type(e).__name__


async def send_email_via_smtp(
    account: SMTPAccount,
    decrypted_password: str,
    message: EmailMessage,
) -> Tuple[bool, Optional[int], str]:
    """
    Send an email message via the configured SMTP account.

    Returns:
        (success, smtp_response_code, response_message)
    """
    hostname = account.smtp_host
    port = account.smtp_port
    username = account.username
    timeout = account.connection_timeout
    mode = account.security_mode

    try:
        ssl_context = _build_ssl_context(validate_certs=True)

        if mode == SecurityMode.SSL_TLS:
            smtp = aiosmtplib.SMTP(
                hostname=hostname,
                port=port,
                use_tls=True,
                tls_context=ssl_context,
                timeout=timeout,
            )
            await smtp.connect()
        elif mode == SecurityMode.STARTTLS:
            smtp = aiosmtplib.SMTP(
                hostname=hostname,
                port=port,
                use_tls=False,
                timeout=timeout,
            )
            await smtp.connect()
            await smtp.starttls(tls_context=ssl_context)
        else:
            smtp = aiosmtplib.SMTP(
                hostname=hostname,
                port=port,
                use_tls=False,
                timeout=timeout,
            )
            await smtp.connect()

        await smtp.login(username, decrypted_password)
        result = await smtp.send_message(message)
        await smtp.quit()

        # aiosmtplib.send_message returns a dict: {recipient: (code, message)}
        # On success, most SMTP servers return 250
        return True, 250, "Message accepted by SMTP server"

    except aiosmtplib.SMTPAuthenticationError as e:
        return False, e.code, f"Authentication failed: {e.message}"
    except aiosmtplib.SMTPRecipientsRefused as e:
        codes = {addr: err.code for addr, err in e.recipients.items()}
        return False, 550, f"Recipients refused: {codes}"
    except aiosmtplib.SMTPDataError as e:
        return False, e.code, f"SMTP data error: {e.message}"
    except aiosmtplib.SMTPConnectError as e:
        return False, None, f"Connection error: {e}"
    except asyncio.TimeoutError:
        return False, None, f"SMTP timeout after {timeout}s"
    except ssl.SSLError as e:
        return False, None, f"TLS error: {e}"
    except Exception as e:
        logger.error("Unexpected SMTP send error: %s", type(e).__name__)
        return False, None, f"Unexpected error: {type(e).__name__}"


def is_permanent_failure(smtp_code: Optional[int]) -> bool:
    """Return True if the SMTP response code indicates a permanent failure."""
    if smtp_code is None:
        return False
    return smtp_code in PERMANENT_FAILURE_CODES
