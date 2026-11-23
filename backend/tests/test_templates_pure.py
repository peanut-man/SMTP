"""Pure unit tests for template rendering service using Jinja2."""
import pytest
from app.services.template_service import (
    render_template,
    extract_template_variables,
    validate_template_syntax,
)


def test_extract_variables():
    content = "Hello {{ name }}, your verification code is {{ code }} for {{ company }}."
    variables = extract_template_variables(content)
    assert set(variables) == {"name", "code", "company"}


def test_extract_variables_empty():
    assert extract_template_variables("") == []
    assert extract_template_variables(None) == []


def test_validate_syntax_valid():
    assert validate_template_syntax("Hello {{ name }}!") is None
    assert validate_template_syntax("Plain text with no variables") is None


def test_validate_syntax_invalid():
    err = validate_template_syntax("Hello {% if unclosed %}...")
    assert err is not None


def test_render_template():
    class DummyTemplate:
        id = "test-tmpl-id"
        subject = "Welcome to {{ platform }}, {{ name }}!"
        html_content = "<h1>Welcome {{ name }}</h1><p>Your team: {{ team }}</p>"
        text_content = "Welcome {{ name }}! Your team is {{ team }}."

    dummy = DummyTemplate()
    result = render_template(dummy, {
        "platform": "MailFlow",
        "name": "Jane Doe",
        "team": "Engineering",
    })

    assert result["subject"] == "Welcome to MailFlow, Jane Doe!"
    assert "Jane Doe" in result["html_content"]
    assert "Engineering" in result["html_content"]
    assert "Jane Doe" in result["text_content"]


def test_render_template_missing_var_raises():
    class DummyTemplate:
        id = "test-tmpl-id"
        subject = "Hello {{ name }}"
        html_content = None
        text_content = None

    dummy = DummyTemplate()
    with pytest.raises(ValueError) as exc:
        render_template(dummy, {})  # 'name' missing
    assert "Template rendering failed" in str(exc.value)
