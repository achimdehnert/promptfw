"""
DjangoTemplateRegistry — optional Django adapter for TemplateRegistry.

Loads promptfw ``PromptTemplate`` objects from a Django ORM queryset, bridging
the gap between database-backed templates (bfagent ``PromptTemplate`` model)
and the promptfw rendering pipeline.

Usage::

    # In Django application code (e.g. apps/writing_hub/services/):
    from promptfw.django_registry import DjangoTemplateRegistry
    from apps.bfagent.models import PromptTemplate as DjangoTemplate

    registry = DjangoTemplateRegistry.from_queryset(
        DjangoTemplate.objects.filter(is_active=True),
        field_map=DjangoTemplateRegistry.BFAGENT_FIELD_MAP,
        strict=True,
    )
    tmpl = registry.get("character_backstory_v1")

Design decisions:
- Django is a soft dependency: ``import django`` is deferred so promptfw
  remains installable without Django.
- ``from_queryset()`` is the single entry point — no magic auto-discovery.
- Field mapping is explicit and overridable via ``field_map`` — no assumptions
  about model layout beyond ``id``/``layer``/``template``.
- ``strict=True`` raises ``ValueError`` on the first unmappable record;
  ``strict=False`` logs a warning and continues (same contract as
  ``TemplateRegistry.from_directory()``).
- bfagent's ``system_prompt`` + ``user_prompt_template`` are split into two
  separate ``PromptTemplate`` objects: SYSTEM layer + TASK layer.  This is
  the canonical promptfw pattern (ADR-001).
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from promptfw.exceptions import TemplateNotFoundError  # noqa: F401  re-exported for convenience
from promptfw.registry import TemplateRegistry
from promptfw.schema import VALID_RESPONSE_FORMATS, PromptTemplate, TemplateLayer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Field-map type alias
# ---------------------------------------------------------------------------

# A FieldMap maps promptfw field names to either:
#   - a string  → attribute name on the ORM object
#   - a callable → (orm_object) -> value  (for derived / computed fields)
FieldMap = dict[str, str | Callable[[Any], Any]]


# ---------------------------------------------------------------------------
# Built-in field maps
# ---------------------------------------------------------------------------

def _bfagent_output_format_to_response_format(obj: Any) -> str | None:
    """Map bfagent ``output_format`` choices to promptfw ``response_format``."""
    mapping = {
        "json": "json_object",
        "structured": "json_schema",
        "text": "text",
        "markdown": "text",  # markdown is rendered as plain text by the LLM
    }
    raw = getattr(obj, "output_format", None)
    if raw is None:
        return None
    result = mapping.get(str(raw).lower())
    if result is None:
        logger.warning("Unknown output_format %r — defaulting to 'text'", raw)
        return "text"
    return result


# Default field map for the bfagent PromptTemplate model.
# Maps promptfw field names → attribute names or callables on the ORM object.
BFAGENT_FIELD_MAP: FieldMap = {
    # id: template_key (e.g. "character_backstory_v1")
    "id": "template_key",
    # template: user_prompt_template (TASK layer); system_prompt is split off
    "template": "user_prompt_template",
    # layer: always TASK for the primary record; SYSTEM split is handled separately
    "layer": lambda obj: TemplateLayer.TASK,
    # variables: union of required + optional
    "variables": lambda obj: list(
        (obj.required_variables or []) + (obj.optional_variables or [])
    ),
    # version: e.g. "1.0" → keep as-is
    "version": "version",
    # response_format: derived from output_format
    "response_format": _bfagent_output_format_to_response_format,
    # output_schema: direct (dict or {} → None)
    "output_schema": lambda obj: obj.output_schema if obj.output_schema else None,
    # phase / task: from category
    "phase": "category",
    "task": "template_key",
    # metadata: description + tags
    "metadata": lambda obj: {
        "description": obj.description or "",
        "tags": obj.tags or [],
        "ab_test_group": obj.ab_test_group or None,
        "language": getattr(obj, "language", None),
    },
}


# ---------------------------------------------------------------------------
# DjangoTemplateRegistry
# ---------------------------------------------------------------------------

class DjangoTemplateRegistry(TemplateRegistry):
    """
    A ``TemplateRegistry`` subclass that loads templates from a Django ORM queryset.

    Each ORM record is converted to one or two ``PromptTemplate`` objects:

    1. **SYSTEM template** (id: ``<template_key>.system``) — from ``system_prompt``.
       Only created if the ORM object has a non-empty ``system_prompt`` attribute.

    2. **TASK template** (id: ``<template_key>``) — from ``user_prompt_template``
       (or whichever field ``field_map["template"]`` resolves to).

    This split follows the ADR-001 5-layer convention: SYSTEM and TASK are
    separate layers that are assembled into a stack by the caller.
    """

    @classmethod
    def from_queryset(
        cls,
        queryset: Any,
        field_map: FieldMap | None = None,
        strict: bool = False,
        split_system_prompt: bool = True,
    ) -> "DjangoTemplateRegistry":
        """Load templates from a Django ORM queryset.

        Args:
            queryset: Any iterable of ORM objects with the expected attributes.
                      Typically ``MyModel.objects.filter(...)``.
            field_map: Mapping from promptfw field names to ORM attribute names
                       or callables.  Defaults to ``BFAGENT_FIELD_MAP``.
            strict: If ``True``, raise ``ValueError`` on the first conversion
                    error instead of logging a warning and skipping the record.
            split_system_prompt: If ``True`` (default), also create a SYSTEM-layer
                ``PromptTemplate`` from ``obj.system_prompt`` (if non-empty).
                The SYSTEM template id is ``<task_id>.system``.

        Returns:
            Populated ``DjangoTemplateRegistry`` instance.

        Raises:
            ValueError: In strict mode, on the first record that cannot be
                        converted to a valid ``PromptTemplate``.
        """
        if field_map is None:
            field_map = BFAGENT_FIELD_MAP

        registry = cls()
        registry._strict = strict
        count = 0

        for obj in queryset:
            try:
                templates = cls._convert_object(
                    obj,
                    field_map=field_map,
                    split_system_prompt=split_system_prompt,
                )
                for tmpl in templates:
                    registry.register(tmpl)
                    count += 1
            except (ValueError, TypeError, AttributeError) as exc:
                obj_repr = _safe_repr(obj)
                msg = f"DjangoTemplateRegistry: failed to convert {obj_repr}: {exc}"
                if strict:
                    raise ValueError(msg) from exc
                logger.warning(msg)

        logger.info("DjangoTemplateRegistry loaded %d templates from queryset", count)
        return registry

    @classmethod
    def _convert_object(
        cls,
        obj: Any,
        field_map: FieldMap,
        split_system_prompt: bool,
    ) -> list[PromptTemplate]:
        """Convert a single ORM object to one or two ``PromptTemplate`` objects.

        Returns a list so that a single ORM record can produce both a SYSTEM
        and a TASK template.

        Raises:
            ValueError: If required fields (``id``, ``template``) resolve to
                        empty/None values.
            AttributeError: If a field_map attribute name does not exist on ``obj``.
        """
        resolved = _resolve_fields(obj, field_map)

        # --- Validate required fields ---
        template_id = resolved.get("id")
        if not template_id:
            raise ValueError(f"field_map['id'] resolved to empty value for {_safe_repr(obj)}")

        task_template_text = resolved.get("template")
        if not task_template_text:
            raise ValueError(
                f"field_map['template'] resolved to empty value for id={template_id!r}"
            )

        # --- Validate and normalise layer ---
        layer = resolved.get("layer", TemplateLayer.TASK)
        if not isinstance(layer, TemplateLayer):
            try:
                layer = TemplateLayer(layer)
            except ValueError:
                raise ValueError(
                    f"Invalid layer {layer!r} for id={template_id!r}. "
                    f"Valid: {[l.value for l in TemplateLayer]}"
                )

        # --- Validate response_format ---
        rf = resolved.get("response_format")
        if rf is not None and rf not in VALID_RESPONSE_FORMATS:
            raise ValueError(
                f"Invalid response_format {rf!r} for id={template_id!r}. "
                f"Valid: {VALID_RESPONSE_FORMATS}"
            )

        # --- Build TASK PromptTemplate ---
        task_kwargs: dict[str, Any] = {
            "id": template_id,
            "layer": layer,
            "template": task_template_text,
        }
        # Optional fields — only include if present in resolved and non-None
        for field in ("variables", "version", "response_format", "output_schema",
                      "phase", "task", "metadata", "cacheable", "tokens_estimate",
                      "format_type"):
            val = resolved.get(field)
            if val is not None:
                task_kwargs[field] = val

        task_tmpl = PromptTemplate(**task_kwargs)
        result = [task_tmpl]

        # --- Optionally build SYSTEM PromptTemplate ---
        if split_system_prompt:
            system_text = _get_attr(obj, "system_prompt", default=None)
            if system_text and str(system_text).strip():
                system_tmpl = PromptTemplate(
                    id=f"{template_id}.system",
                    layer=TemplateLayer.SYSTEM,
                    template=str(system_text),
                    cacheable=True,
                    version=resolved.get("version", "1.0.0"),
                    metadata=resolved.get("metadata") or {},
                )
                result.insert(0, system_tmpl)

        return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_fields(obj: Any, field_map: FieldMap) -> dict[str, Any]:
    """Resolve all entries in a field_map against an ORM object."""
    resolved: dict[str, Any] = {}
    for promptfw_field, source in field_map.items():
        if callable(source):
            resolved[promptfw_field] = source(obj)
        else:
            resolved[promptfw_field] = _get_attr(obj, str(source), default=None)
    return resolved


def _get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """Safe attribute access — returns ``default`` if attr is missing."""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


def _safe_repr(obj: Any) -> str:
    """Compact repr of an ORM object for log messages."""
    try:
        pk = getattr(obj, "pk", None) or getattr(obj, "id", None)
        cls_name = type(obj).__name__
        key = getattr(obj, "template_key", None) or getattr(obj, "name", None)
        parts = [cls_name]
        if pk is not None:
            parts.append(f"pk={pk}")
        if key:
            parts.append(f"key={key!r}")
        return f"<{' '.join(parts)}>"
    except Exception:
        return repr(obj)
