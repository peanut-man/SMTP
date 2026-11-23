from __future__ import annotations
"""Jinja2 template rendering service."""
import logging
import re
from typing import Any, Dict, Optional, List, TYPE_CHECKING

from jinja2 import (
    Environment,
    BaseLoader,
    TemplateError,
    Undefined,
    StrictUndefined,
    select_autoescape,
)

try:
    from app.models.email_template import EmailTemplate
except ImportError:
    EmailTemplate = Any  # type: ignore

logger = logging.getLogger(__name__)

# Restricted Jinja2 environment — no file system access, no dangerous globals
_jinja_env = Environment(
    loader=BaseLoader(),
    autoescape=select_autoescape(["html", "xml"]),
    undefined=StrictUndefined,
    # Disable dangerous extensions
)

# Strip unsafe globals
_jinja_env.globals = {
    "range": range,
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
}


def render_template(
    template: EmailTemplate,
    variables: Dict[str, Any],
) -> Dict[str, Optional[str]]:
    """
    Render a template with the provided variables.
    Returns dict with keys: subject, html_content, text_content.
    """
    result = {}

    try:
        if template.subject:
            tmpl = _jinja_env.from_string(template.subject)
            result["subject"] = tmpl.render(**variables)
        else:
            result["subject"] = template.subject

        if template.html_content:
            tmpl = _jinja_env.from_string(template.html_content)
            result["html_content"] = tmpl.render(**variables)
        else:
            result["html_content"] = template.html_content

        if template.text_content:
            tmpl = _jinja_env.from_string(template.text_content)
            result["text_content"] = tmpl.render(**variables)
        else:
            result["text_content"] = template.text_content

    except TemplateError as e:
        logger.warning("Template rendering error for template %s: %s", template.id, str(e))
        raise ValueError(f"Template rendering failed: {str(e)}")

    return result


def extract_template_variables(content: str) -> List[str]:
    """Extract Jinja2 variable names from a template string."""
    if not content:
        return []
    # Match {{ variable }} patterns
    pattern = r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}"
    return list(set(re.findall(pattern, content)))


def validate_template_syntax(content: str) -> Optional[str]:
    """
    Validate Jinja2 template syntax.
    Returns None if valid, or an error message string.
    """
    try:
        _jinja_env.parse(content)
        return None
    except TemplateError as e:
        return str(e)
