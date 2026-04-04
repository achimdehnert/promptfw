"""
PromptTemplate — DB-managed prompt template model (ADR-146).

Platform-standard fields: BigAutoField, public_id, tenant_id, deleted_at.
Pydantic v2 validation for JSONFields in clean().
"""

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


# --- Pydantic v2 Schemas for JSONField validation ---

try:
    from pydantic import BaseModel, Field
    from typing import Any

    class PromptVariableSchema(BaseModel):
        type: str
        required: bool = False
        default: Any = None
        description: str = ""
        enum: list[str] | None = None
        min: int | None = None
        max: int | None = None

    class PromptVariablesSchema(BaseModel):
        variables: dict[str, PromptVariableSchema] = Field(default_factory=dict)

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False


# --- Enums ---

class HubChoices(models.TextChoices):
    WRITING = "writing-hub", _("Writing Hub")
    TRAVEL_BEAT = "travel-beat", _("Travel Beat / DriftTales")
    RESEARCH = "research-hub", _("Research Hub")
    CAD = "cad-hub", _("CAD Hub")
    RISK = "risk-hub", _("Risk Hub")
    COACH = "coach-hub", _("Coach Hub")
    OTHER = "other", _("Other / Platform-wide")


class ResponseFormat(models.TextChoices):
    TEXT = "text", _("Text")
    JSON_OBJECT = "json_object", _("JSON Object")
    JSON_SCHEMA = "json_schema", _("JSON Schema")


# --- action_code Convention Validator ---

action_code_validator = RegexValidator(
    regex=r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*){1,3}$",
    message=_('Format: "{hub}.{domain}.{action}" — lowercase, digits, hyphens only'),
)


class PromptTemplate(models.Model):
    """DB-managed prompt template with CRUD, versioning, defaults, and variable schema.

    Resolution order (via render_prompt()):
      1. DB: PromptTemplate.objects.filter(action_code=X, is_active=True)
      2. File: settings.PROMPTFW_PROMPTS_DIR / f"{action_code}.jinja2"
      3. Error: PromptNotFoundError
    """

    # === Platform-Standard Fields ===
    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_("public ID"),
    )
    # tenant_id present from Phase 1, active only when PROMPTFW_MULTI_TENANT=True.
    # See ADR-146 Section 5.7 for multi-tenancy strategy.
    tenant_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("tenant ID"),
        help_text=_(
            "Multi-tenancy isolation (null = platform-wide). "
            "Active only when settings.PROMPTFW_MULTI_TENANT=True."
        ),
    )

    # === Identity ===
    action_code = models.CharField(
        max_length=100,
        db_index=True,
        validators=[action_code_validator],
        verbose_name=_("action code"),
        help_text=_(
            'Unique prompt identifier. Convention: "{hub}.{domain}.{action}" '
            'e.g. "travel-beat.story.chapter", "writing-hub.authoring.chapter-write"'
        ),
    )
    version = models.PositiveIntegerField(
        default=1,
        verbose_name=_("version"),
    )

    # === Content (Jinja2 Templates) ===
    system_template = models.TextField(
        blank=True,
        verbose_name=_("system template"),
        help_text=_("System prompt (Jinja2). Variables: {{ var_name }}. Empty = no system prompt."),
    )
    user_template = models.TextField(
        verbose_name=_("user template"),
        help_text=_("User prompt (Jinja2). Variables: {{ var_name }}. Required."),
    )

    # === Parametrization ===
    defaults = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("defaults"),
        help_text=_("Default values when caller does not provide them."),
    )
    variables_schema = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("variables schema"),
        help_text=_(
            "Variable schema (Pydantic-validated). "
            'e.g. {"genre": {"type": "string", "required": true}}'
        ),
    )

    # === LLM Hints (optional — aifw remains routing SSoT) ===
    suggested_max_tokens = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("suggested max tokens"),
        help_text=_("Suggested max_tokens. Passed as llm_overrides to aifw."),
    )
    suggested_temperature = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)],
        verbose_name=_("suggested temperature"),
        help_text=_("Suggested temperature (0.0-2.0)."),
    )
    response_format = models.CharField(
        max_length=20,
        blank=True,
        choices=ResponseFormat.choices,
        verbose_name=_("response format"),
        help_text=_("Expected response format."),
    )
    output_schema = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("output schema"),
        help_text=_("JSON Schema when response_format=json_schema."),
    )

    # === Metadata ===
    name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("name"),
        help_text=_("Human-readable name"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("description"),
        help_text=_("What does this prompt do?"),
    )
    hub = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        choices=HubChoices.choices,
        verbose_name=_("hub"),
    )
    domain = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        verbose_name=_("domain"),
        help_text=_("Domain: story, authoring, research, worlds"),
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("tags"),
    )

    # === Lifecycle ===
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("is active"),
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("deleted at"),
        help_text=_("Soft-delete timestamp (null = not deleted)"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("notes"),
        help_text=_("Internal notes / change reason"),
    )

    # CharField instead of ForeignKey — avoids migration dependency on AUTH_USER_MODEL
    created_by = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_("created by"),
        help_text=_("Username of creator"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "promptfw"
        db_table = "promptfw_template"
        ordering = ["action_code", "-version"]
        verbose_name = _("prompt template")
        verbose_name_plural = _("prompt templates")
        constraints = [
            models.UniqueConstraint(
                fields=["action_code", "version"],
                name="promptfw_template_action_version_uniq",
            ),
            # Enforces max 1 is_active=True per action_code at DB level.
            # For multi-tenancy, this constraint must be extended to
            # (action_code, tenant_id) via migration.
            models.UniqueConstraint(
                fields=["action_code"],
                condition=models.Q(is_active=True),
                name="promptfw_template_action_active_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["hub", "is_active"]),
            models.Index(fields=["domain", "is_active"]),
            models.Index(fields=["action_code", "is_active", "-version"]),
            models.Index(fields=["tenant_id", "is_active"]),
        ]

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.action_code} v{self.version} ({status})"

    def clean(self):
        """Pydantic v2 validation for JSONFields."""
        from django.core.exceptions import ValidationError

        if HAS_PYDANTIC and self.variables_schema:
            from pydantic import ValidationError as PydanticValidationError

            try:
                PromptVariablesSchema(variables=self.variables_schema)
            except PydanticValidationError as e:
                raise ValidationError({"variables_schema": str(e)})

        # Cross-validation: defaults keys must exist in schema
        if self.variables_schema and self.defaults:
            unknown = set(self.defaults.keys()) - set(self.variables_schema.keys())
            if unknown:
                raise ValidationError(
                    {"defaults": f"Keys not in variables_schema: {unknown}"}
                )
