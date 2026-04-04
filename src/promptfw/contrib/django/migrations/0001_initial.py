"""
Initial migration for promptfw.contrib.django — PromptTemplate model (ADR-146).

Uses SeparateDatabaseAndState pattern for compatibility with existing
bfagent legacy tables if needed.
"""

import uuid

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PromptTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                (
                    "public_id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="public ID",
                    ),
                ),
                (
                    "tenant_id",
                    models.BigIntegerField(
                        blank=True,
                        db_index=True,
                        help_text=(
                            "Multi-tenancy isolation (null = platform-wide). "
                            "Active only when settings.PROMPTFW_MULTI_TENANT=True."
                        ),
                        null=True,
                        verbose_name="tenant ID",
                    ),
                ),
                (
                    "action_code",
                    models.CharField(
                        db_index=True,
                        help_text=(
                            'Unique prompt identifier. Convention: "{hub}.{domain}.{action}" '
                            'e.g. "travel-beat.story.chapter", '
                            '"writing-hub.authoring.chapter-write"'
                        ),
                        max_length=100,
                        validators=[
                            django.core.validators.RegexValidator(
                                message=(
                                    'Format: "{hub}.{domain}.{action}" '
                                    "— lowercase, digits, hyphens only"
                                ),
                                regex=r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*){1,3}$",
                            )
                        ],
                        verbose_name="action code",
                    ),
                ),
                (
                    "version",
                    models.PositiveIntegerField(default=1, verbose_name="version"),
                ),
                (
                    "system_template",
                    models.TextField(
                        blank=True,
                        help_text=(
                            "System prompt (Jinja2). Variables: {{ var_name }}. "
                            "Empty = no system prompt."
                        ),
                        verbose_name="system template",
                    ),
                ),
                (
                    "user_template",
                    models.TextField(
                        help_text=(
                            "User prompt (Jinja2). Variables: {{ var_name }}. Required."
                        ),
                        verbose_name="user template",
                    ),
                ),
                (
                    "defaults",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Default values when caller does not provide them.",
                        verbose_name="defaults",
                    ),
                ),
                (
                    "variables_schema",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "Variable schema (Pydantic-validated). "
                            'e.g. {"genre": {"type": "string", "required": true}}'
                        ),
                        verbose_name="variables schema",
                    ),
                ),
                (
                    "suggested_max_tokens",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Suggested max_tokens. Passed as llm_overrides to aifw.",
                        null=True,
                        verbose_name="suggested max tokens",
                    ),
                ),
                (
                    "suggested_temperature",
                    models.FloatField(
                        blank=True,
                        help_text="Suggested temperature (0.0-2.0).",
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(0.0),
                            django.core.validators.MaxValueValidator(2.0),
                        ],
                        verbose_name="suggested temperature",
                    ),
                ),
                (
                    "response_format",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("text", "Text"),
                            ("json_object", "JSON Object"),
                            ("json_schema", "JSON Schema"),
                        ],
                        help_text="Expected response format.",
                        max_length=20,
                        verbose_name="response format",
                    ),
                ),
                (
                    "output_schema",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="JSON Schema when response_format=json_schema.",
                        verbose_name="output schema",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="Human-readable name",
                        max_length=200,
                        verbose_name="name",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="What does this prompt do?",
                        verbose_name="description",
                    ),
                ),
                (
                    "hub",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("writing-hub", "Writing Hub"),
                            ("travel-beat", "Travel Beat / DriftTales"),
                            ("research-hub", "Research Hub"),
                            ("cad-hub", "CAD Hub"),
                            ("risk-hub", "Risk Hub"),
                            ("coach-hub", "Coach Hub"),
                            ("other", "Other / Platform-wide"),
                        ],
                        db_index=True,
                        max_length=50,
                        verbose_name="hub",
                    ),
                ),
                (
                    "domain",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="Domain: story, authoring, research, worlds",
                        max_length=50,
                        verbose_name="domain",
                    ),
                ),
                (
                    "tags",
                    models.JSONField(
                        blank=True,
                        default=list,
                        verbose_name="tags",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        verbose_name="is active",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Soft-delete timestamp (null = not deleted)",
                        null=True,
                        verbose_name="deleted at",
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True,
                        help_text="Internal notes / change reason",
                        verbose_name="notes",
                    ),
                ),
                (
                    "created_by",
                    models.CharField(
                        blank=True,
                        help_text="Username of creator",
                        max_length=150,
                        verbose_name="created by",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
            ],
            options={
                "verbose_name": "prompt template",
                "verbose_name_plural": "prompt templates",
                "db_table": "promptfw_template",
                "ordering": ["action_code", "-version"],
            },
        ),
        migrations.AddConstraint(
            model_name="prompttemplate",
            constraint=models.UniqueConstraint(
                fields=("action_code", "version"),
                name="promptfw_template_action_version_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="prompttemplate",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_active", True)),
                fields=("action_code",),
                name="promptfw_template_action_active_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="prompttemplate",
            index=models.Index(
                fields=["hub", "is_active"],
                name="promptfw_te_hub_is_ac_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="prompttemplate",
            index=models.Index(
                fields=["domain", "is_active"],
                name="promptfw_te_domain_is_ac_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="prompttemplate",
            index=models.Index(
                fields=["action_code", "is_active", "-version"],
                name="promptfw_te_action_is_ac_ver_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="prompttemplate",
            index=models.Index(
                fields=["tenant_id", "is_active"],
                name="promptfw_te_tenant_is_ac_idx",
            ),
        ),
    ]
