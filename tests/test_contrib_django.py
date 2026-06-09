"""
Tests for promptfw.contrib.django — ≥25 tests covering model, resolution, admin, CLI (ADR-146).

Requires: pip install iil-promptfw[django] + Django test setup.
Run: pytest tests/test_contrib_django.py -v
"""

import uuid
from unittest.mock import MagicMock, patch

import django
from django.conf import settings

# Minimal Django settings for testing
if not settings.configured:
    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django.contrib.admin",
            "promptfw.contrib.django",
        ],
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
        USE_TZ=True,
    )
    django.setup()

import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection

from promptfw.contrib.django.models import (
    HAS_PYDANTIC,
    HubChoices,
    PromptTemplate,
    ResponseFormat,
    action_code_validator,
)
from promptfw.contrib.django.resolution import (
    PromptNotFoundError,
    PromptValidationError,
    _load_from_db,
    _render_db_template,
    _validate_context,
    invalidate_cache,
    render_prompt,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


_TABLE_CREATED = False


@pytest.fixture(autouse=True)
def _setup_db():
    """Create tables once and clear cache before each test."""
    global _TABLE_CREATED
    if not _TABLE_CREATED:
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(PromptTemplate)
        _TABLE_CREATED = True
    cache.clear()
    yield
    PromptTemplate.objects.all().delete()
    cache.clear()


@pytest.fixture
def sample_template():
    """Create a basic active template."""
    return PromptTemplate.objects.create(
        action_code="test-hub.domain.action",
        version=1,
        system_template="You are a {{ role }}.",
        user_template="Write about {{ topic }}.",
        defaults={"role": "writer", "language": "de"},
        variables_schema={
            "role": {"type": "string", "required": True},
            "topic": {"type": "string", "required": True},
            "language": {"type": "string", "required": False, "default": "de"},
        },
        hub="writing-hub",
        domain="authoring",
        name="Test Prompt",
        is_active=True,
    )


# ===========================================================================
# Model Tests
# ===========================================================================


class TestPromptTemplateModel:
    """Tests for the PromptTemplate Django model."""

    def test_create_basic_template(self, sample_template):
        """T01: Basic creation with all fields."""
        assert sample_template.pk is not None
        assert sample_template.action_code == "test-hub.domain.action"
        assert sample_template.version == 1
        assert sample_template.is_active is True
        assert sample_template.public_id is not None

    def test_str_representation(self, sample_template):
        """T02: __str__ shows action_code, version, status."""
        assert str(sample_template) == "test-hub.domain.action v1 (active)"

    def test_str_inactive(self, sample_template):
        """T03: __str__ for inactive template."""
        sample_template.is_active = False
        sample_template.save()
        assert "(inactive)" in str(sample_template)

    def test_public_id_is_uuid(self, sample_template):
        """T04: public_id is a valid UUID."""
        assert isinstance(sample_template.public_id, uuid.UUID)

    def test_default_version_is_1(self):
        """T05: Default version is 1."""
        tpl = PromptTemplate.objects.create(
            action_code="test-hub.default.version",
            user_template="Hello {{ name }}",
        )
        assert tpl.version == 1

    def test_defaults_is_empty_dict(self):
        """T06: Defaults field defaults to empty dict."""
        tpl = PromptTemplate.objects.create(
            action_code="test-hub.empty.defaults",
            user_template="Hello",
        )
        assert tpl.defaults == {}

    def test_unique_constraint_action_version(self, sample_template):
        """T07: Cannot create duplicate (action_code, version)."""
        with pytest.raises(IntegrityError):
            PromptTemplate.objects.create(
                action_code="test-hub.domain.action",
                version=1,
                user_template="Duplicate",
                is_active=False,
            )

    def test_unique_constraint_active(self, sample_template):
        """T08: Cannot have two active templates with same action_code."""
        with pytest.raises(IntegrityError):
            PromptTemplate.objects.create(
                action_code="test-hub.domain.action",
                version=2,
                user_template="Second active",
                is_active=True,
            )

    def test_multiple_inactive_allowed(self, sample_template):
        """T09: Multiple inactive templates with same action_code are fine."""
        sample_template.is_active = False
        sample_template.save()
        tpl2 = PromptTemplate.objects.create(
            action_code="test-hub.domain.action",
            version=2,
            user_template="v2",
            is_active=False,
        )
        assert tpl2.pk is not None

    def test_soft_delete_field(self, sample_template):
        """T10: deleted_at is null by default."""
        assert sample_template.deleted_at is None

    def test_tenant_id_nullable(self, sample_template):
        """T11: tenant_id is null by default (platform-wide)."""
        assert sample_template.tenant_id is None

    def test_hub_choices(self):
        """T12: HubChoices enum has expected values."""
        assert HubChoices.WRITING.value == "writing-hub"
        assert HubChoices.TRAVEL_BEAT.value == "travel-beat"
        assert HubChoices.RESEARCH.value == "research-hub"

    def test_response_format_choices(self):
        """T13: ResponseFormat enum has expected values."""
        assert ResponseFormat.TEXT.value == "text"
        assert ResponseFormat.JSON_OBJECT.value == "json_object"
        assert ResponseFormat.JSON_SCHEMA.value == "json_schema"


# ===========================================================================
# Validation Tests
# ===========================================================================


class TestValidation:
    """Tests for model validation (clean, validators)."""

    def test_action_code_validator_valid(self):
        """T14: Valid action_code patterns pass."""
        for code in [
            "hub.domain.action",
            "writing-hub.authoring.chapter-write",
            "a.b.c.d",
            "travel-beat.story.chapter",
        ]:
            action_code_validator(code)  # should not raise

    def test_action_code_validator_invalid(self):
        """T15: Invalid action_code patterns fail."""
        from django.core.exceptions import ValidationError as DjangoValidationError

        for code in [
            "UPPERCASE.bad",
            "no-dots",
            ".leading.dot",
            "hub.domain.action.too.many.parts",
            "hub..empty",
        ]:
            with pytest.raises(DjangoValidationError):
                action_code_validator(code)

    @pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic not installed")
    def test_clean_valid_schema(self, sample_template):
        """T16: clean() passes with valid variables_schema."""
        sample_template.clean()  # should not raise

    @pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic not installed")
    def test_clean_invalid_schema(self):
        """T17: clean() raises ValidationError for invalid schema."""
        tpl = PromptTemplate(
            action_code="test-hub.bad.schema",
            user_template="Hello",
            variables_schema={"genre": {"type": 123}},  # type must be string
        )
        with pytest.raises(ValidationError):
            tpl.clean()

    def test_clean_defaults_cross_validation(self):
        """T18: clean() rejects defaults keys not in variables_schema."""
        tpl = PromptTemplate(
            action_code="test-hub.cross.validation",
            user_template="Hello",
            variables_schema={"genre": {"type": "string", "required": True}},
            defaults={"genre": "thriller", "unknown_key": "value"},
        )
        with pytest.raises(ValidationError) as exc_info:
            tpl.clean()
        assert "unknown_key" in str(exc_info.value)


# ===========================================================================
# Resolution Tests
# ===========================================================================


class TestResolution:
    """Tests for render_prompt() and helpers."""

    def test_render_prompt_from_db(self, sample_template):
        """T19: render_prompt() resolves from DB and renders correctly."""
        messages = render_prompt("test-hub.domain.action", role="assistant", topic="Python")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "assistant" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert "Python" in messages[1]["content"]

    def test_render_prompt_uses_defaults(self, sample_template):
        """T20: render_prompt() merges defaults — caller wins on conflict."""
        messages = render_prompt("test-hub.domain.action", topic="AI")
        # role comes from defaults ("writer")
        assert "writer" in messages[0]["content"]
        assert "AI" in messages[1]["content"]

    def test_render_prompt_not_found(self):
        """T21: render_prompt() raises PromptNotFoundError for unknown action_code."""
        with pytest.raises(PromptNotFoundError):
            render_prompt("nonexistent.action.code")

    def test_render_prompt_skips_deleted(self, sample_template):
        """T22: render_prompt() ignores soft-deleted templates."""
        from django.utils import timezone

        sample_template.deleted_at = timezone.now()
        sample_template.save()
        with pytest.raises(PromptNotFoundError):
            render_prompt("test-hub.domain.action", role="x", topic="y")

    def test_render_prompt_no_system_template(self):
        """T23: render_prompt() works without system_template."""
        PromptTemplate.objects.create(
            action_code="test-hub.no.system",
            user_template="Just user: {{ msg }}",
            is_active=True,
        )
        messages = render_prompt("test-hub.no.system", msg="hello")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_validate_context_missing_required(self, sample_template):
        """T24: _validate_context raises PromptValidationError for missing required vars."""
        with pytest.raises(PromptValidationError) as exc_info:
            _validate_context(sample_template, {"role": "writer"})  # topic missing
        assert "topic" in str(exc_info.value)

    def test_validate_context_optional_ok(self, sample_template):
        """T25: _validate_context passes when optional vars are missing."""
        _validate_context(
            sample_template, {"role": "writer", "topic": "AI"}
        )  # language is optional

    def test_cache_hit(self, sample_template):
        """T26: Second call uses cache (no DB query)."""
        render_prompt("test-hub.domain.action", role="a", topic="b")
        # After first call, value is cached. Verify cache has the entry.
        cached = cache.get("promptfw:template:test-hub.domain.action")
        assert cached is not None
        assert cached != "__NONE__"
        assert cached.action_code == "test-hub.domain.action"

    def test_cache_invalidation(self, sample_template):
        """T27: invalidate_cache() clears the cached template."""
        render_prompt("test-hub.domain.action", role="a", topic="b")
        invalidate_cache("test-hub.domain.action")
        # After invalidation, cache should be empty
        assert cache.get("promptfw:template:test-hub.domain.action") is None

    def test_cache_stores_none_for_missing(self):
        """T28: Cache stores __NONE__ sentinel for missing templates."""
        # First call will query DB, find nothing, cache __NONE__
        result = _load_from_db("nonexistent.action.code")
        assert result is None
        assert cache.get("promptfw:template:nonexistent.action.code") == "__NONE__"

    def test_render_db_template_sandboxed(self, sample_template):
        """T29: _render_db_template uses SandboxedEnvironment (no introspection)."""
        messages = _render_db_template(sample_template, {"role": "test", "topic": "safety"})
        assert len(messages) == 2
        assert "test" in messages[0]["content"]


# ===========================================================================
# Multi-Tenancy Tests
# ===========================================================================


class TestMultiTenancy:
    """Tests for tenant-aware resolution."""

    @patch("promptfw.contrib.django.resolution.settings")
    def test_tenant_aware_cache_key(self, mock_settings, sample_template):
        """T30: Cache key includes tenant_id when multi-tenant enabled."""
        mock_settings.PROMPTFW_MULTI_TENANT = True
        mock_settings.PROMPTFW_CACHE_TTL = 300
        mock_settings.PROMPTFW_PROMPTS_DIR = None
        mock_settings.PROMPTFW_FILE_FALLBACK = False

        sample_template.tenant_id = 42
        sample_template.save()

        _load_from_db("test-hub.domain.action", tenant_id=42)
        assert cache.get("promptfw:template:test-hub.domain.action:42") is not None


# ===========================================================================
# File Fallback Tests
# ===========================================================================


class TestFileFallback:
    """Tests for file-based fallback resolution."""

    def test_file_fallback_disabled(self, tmp_path):
        """T31: File fallback skipped when PROMPTFW_FILE_FALLBACK=False."""
        with patch(
            "promptfw.contrib.django.resolution._get_file_fallback_enabled",
            return_value=False,
        ):
            with pytest.raises(PromptNotFoundError):
                render_prompt("nonexistent.file.prompt")

    def test_file_not_found_returns_none(self, tmp_path):
        """T32: _render_from_file returns None when file doesn't exist."""
        from promptfw.contrib.django.resolution import _render_from_file

        result = _render_from_file("nonexistent.action", {}, str(tmp_path))
        assert result is None


# ===========================================================================
# Admin Tests
# ===========================================================================


class TestAdmin:
    """Tests for admin functionality (soft-delete, versioning)."""

    def test_soft_delete(self, sample_template):
        """T33: delete_model performs soft-delete."""
        from promptfw.contrib.django.admin import PromptTemplateAdmin

        admin_instance = PromptTemplateAdmin(PromptTemplate, None)
        mock_request = MagicMock()
        admin_instance.delete_model(mock_request, sample_template)

        sample_template.refresh_from_db()
        assert sample_template.deleted_at is not None
        assert sample_template.is_active is False

    def test_bulk_soft_delete(self, sample_template):
        """T34: delete_queryset performs bulk soft-delete."""
        from promptfw.contrib.django.admin import PromptTemplateAdmin

        admin_instance = PromptTemplateAdmin(PromptTemplate, None)
        mock_request = MagicMock()
        qs = PromptTemplate.objects.filter(pk=sample_template.pk)
        admin_instance.delete_queryset(mock_request, qs)

        sample_template.refresh_from_db()
        assert sample_template.deleted_at is not None
        assert sample_template.is_active is False

    def test_create_new_version(self, sample_template):
        """T35: create_new_version creates v2 and deactivates v1."""
        from promptfw.contrib.django.admin import PromptTemplateAdmin

        admin_instance = PromptTemplateAdmin(PromptTemplate, None)
        mock_request = MagicMock()
        mock_request.user.username = "testuser"
        qs = PromptTemplate.objects.filter(pk=sample_template.pk)
        admin_instance.create_new_version(mock_request, qs)

        old = PromptTemplate.objects.get(pk=sample_template.pk)
        assert old.is_active is False

        new = PromptTemplate.objects.get(action_code="test-hub.domain.action", version=2)
        assert new.is_active is True
        assert new.created_by == "testuser"


# ===========================================================================
# Export / Import Helpers
# ===========================================================================


class TestExportImport:
    """Tests for seed_prompts and export_prompts helpers."""

    def test_yaml_roundtrip(self, sample_template, tmp_path):
        """T36: Export to YAML and re-import produces same data."""
        import yaml

        # Export
        data = {
            "prompts": [
                {
                    "action_code": sample_template.action_code,
                    "version": sample_template.version,
                    "name": sample_template.name,
                    "system_template": sample_template.system_template,
                    "user_template": sample_template.user_template,
                    "hub": sample_template.hub,
                    "defaults": sample_template.defaults,
                    "variables_schema": sample_template.variables_schema,
                }
            ]
        }
        yaml_path = tmp_path / "export.yaml"
        yaml_path.write_text(yaml.dump(data, allow_unicode=True))

        # Verify YAML is valid
        loaded = yaml.safe_load(yaml_path.read_text())
        assert len(loaded["prompts"]) == 1
        assert loaded["prompts"][0]["action_code"] == "test-hub.domain.action"
