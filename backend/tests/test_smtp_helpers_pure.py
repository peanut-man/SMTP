"""Pure unit tests for SMTP helper functions and logic."""
import pytest

try:
    from app.services.smtp_service import is_permanent_failure, PERMANENT_FAILURE_CODES, TEMPORARY_FAILURE_CODES
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

pytestmark = pytest.mark.skipif(not HAS_DEPS, reason="aiosmtplib or dependencies not installed")


def test_permanent_failure_codes():
    for code in [500, 501, 503, 530, 535, 550, 551, 552, 553, 554]:
        assert is_permanent_failure(code) is True, f"Expected {code} to be permanent"


def test_temporary_failure_codes():
    for code in [421, 450, 451, 452]:
        assert is_permanent_failure(code) is False, f"Expected {code} to NOT be permanent"


def test_none_failure_code():
    assert is_permanent_failure(None) is False


def test_success_code():
    assert is_permanent_failure(250) is False
