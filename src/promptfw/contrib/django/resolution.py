"""
Prompt resolution API — render_prompt() with DB → File → Error fallback (ADR-146).

Cache layer with configurable TTL, SandboxedEnvironment for Jinja2,
schema validation for required variables, tenant-aware when enabled.
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db import models
from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

logger = logging.getLogger(__name__)

_JINJA_ENV = SandboxedEnvironment(undefined=StrictUndefined)

_DEFAULT_CACHE_TTL = 300  # 5 minutes


class PromptNotFoundError(Exception):
    """Raised when no prompt template found for action_code."""


class PromptValidationError(Exception):
    """Raised when required variables are missing or invalid."""


# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------


def _get_prompts_dir():
    return getattr(settings, "PROMPTFW_PROMPTS_DIR", None)


def _get_cache_ttl():
    return getattr(settings, "PROMPTFW_CACHE_TTL", _DEFAULT_CACHE_TTL)


def _get_file_fallback_enabled():
    return getattr(settings, "PROMPTFW_FILE_FALLBACK", True)


def _is_multi_tenant():
    return getattr(settings, "PROMPTFW_MULTI_TENANT", False)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_prompt(
    action_code: str, *, tenant_id: int | None = None, **context: Any
) -> list[dict[str, str]]:
    """
    Unified prompt resolution — single API for all hubs.

    Resolution order:
      1. DB: PromptTemplate(action_code=X, is_active=True, latest version)
      2. File: settings.PROMPTFW_PROMPTS_DIR / f"{action_code}.jinja2" (if enabled)
      3. Error: PromptNotFoundError

    Variable merging: defaults (from DB) | context (from caller) — caller wins.
    Schema validation: required variables checked if variables_schema is defined.

    Args:
        action_code: Prompt identifier (e.g. "writing-hub.authoring.chapter-write")
        tenant_id: Optional tenant isolation (only when PROMPTFW_MULTI_TENANT=True)
        **context: Variables to render into the template

    Returns:
        [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
    """
    # 1. DB lookup (cached, tenant-aware when enabled)
    tpl = _load_from_db(action_code, tenant_id=tenant_id)
    if tpl:
        merged = {**tpl.defaults, **context}
        _validate_context(tpl, merged)
        return _render_db_template(tpl, merged)

    # 2. File fallback (disableable via settings.PROMPTFW_FILE_FALLBACK=False)
    prompts_dir = _get_prompts_dir()
    if prompts_dir and _get_file_fallback_enabled():
        messages = _render_from_file(action_code, context, str(prompts_dir))
        if messages:
            return messages

    # 3. Error
    raise PromptNotFoundError(
        f"No prompt template found for action_code='{action_code}'. "
        f"Neither in DB (promptfw_template) nor in files ({prompts_dir})."
    )


def invalidate_cache(action_code: str, tenant_id: int | None = None) -> None:
    """Invalidate cached template for an action_code. Called by Admin on save/delete."""
    suffix = f":{tenant_id}" if _is_multi_tenant() and tenant_id else ""
    cache_key = f"promptfw:template:{action_code}{suffix}"
    cache.delete(cache_key)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_context(tpl, merged: dict) -> None:
    """Validate merged context against variables_schema (if defined)."""
    if not tpl.variables_schema:
        return
    for var_name, spec in tpl.variables_schema.items():
        if spec.get("required") and var_name not in merged:
            raise PromptValidationError(
                f"Required variable '{var_name}' missing for "
                f"action_code='{tpl.action_code}'. "
                f"Expected variables: {list(tpl.variables_schema.keys())}"
            )


def _load_from_db(action_code: str, *, tenant_id: int | None = None):
    """Load active template from DB (latest version) with cache.

    Cache key is tenant-aware when PROMPTFW_MULTI_TENANT=True.
    """
    suffix = f":{tenant_id}" if _is_multi_tenant() and tenant_id else ""
    cache_key = f"promptfw:template:{action_code}{suffix}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached if cached != "__NONE__" else None

    from promptfw.contrib.django.models import PromptTemplate

    qs = PromptTemplate.objects.filter(
        action_code=action_code,
        is_active=True,
        deleted_at__isnull=True,
    )
    if _is_multi_tenant() and tenant_id is not None:
        qs = qs.filter(models.Q(tenant_id=tenant_id) | models.Q(tenant_id__isnull=True))
    tpl = qs.order_by("-version").first()

    cache.set(cache_key, tpl if tpl else "__NONE__", timeout=_get_cache_ttl())
    return tpl


def _render_db_template(tpl, context: dict) -> list[dict[str, str]]:
    """Render DB template with SandboxedEnvironment."""
    messages = []
    if tpl.system_template:
        sys_rendered = _JINJA_ENV.from_string(tpl.system_template).render(**context).strip()
        if sys_rendered:
            messages.append({"role": "system", "content": sys_rendered})

    user_rendered = _JINJA_ENV.from_string(tpl.user_template).render(**context).strip()
    messages.append({"role": "user", "content": user_rendered})
    return messages


def _render_from_file(action_code: str, context: dict, prompts_dir: str):
    """Fallback: render from .jinja2 frontmatter file.

    No silent degradation: rendering errors are NOT swallowed.
    Only 'file not found' returns None (= continue to Error).
    """
    from pathlib import Path

    path = Path(prompts_dir) / f"{action_code.replace('.', '/')}.jinja2"
    if not path.exists():
        path = Path(prompts_dir) / f"{action_code}.jinja2"
    if not path.exists():
        return None

    # File exists → rendering MUST succeed, otherwise propagate error
    try:
        from promptfw.frontmatter import render_frontmatter_file

        return render_frontmatter_file(str(path), context)
    except ImportError:
        logger.warning(
            "promptfw.frontmatter not available — cannot render file fallback for %s",
            action_code,
        )
        return None
