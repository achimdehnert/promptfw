"""
Tests for DjangoTemplateRegistry — no Django dependency required.

Uses plain Python objects (SimpleNamespace / dataclasses) to simulate ORM
objects, ensuring the registry can be tested without a Django environment.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from promptfw.django_registry import (
    BFAGENT_FIELD_MAP,
    DjangoTemplateRegistry,
    _bfagent_output_format_to_response_format,
    _safe_repr,
)
from promptfw.exceptions import TemplateNotFoundError
from promptfw.schema import PromptTemplate, TemplateLayer


# ---------------------------------------------------------------------------
# Helpers — build mock ORM objects
# ---------------------------------------------------------------------------

def _make_bfagent_obj(**kwargs) -> SimpleNamespace:
    """Return a SimpleNamespace mimicking a bfagent PromptTemplate ORM object."""
    defaults = {
        "pk": 1,
        "template_key": "test.task.write",
        "system_prompt": "You are a professional writer.",
        "user_prompt_template": "Write a chapter about {{ topic }}.",
        "required_variables": ["topic"],
        "optional_variables": ["style"],
        "variable_defaults": {},
        "output_format": "text",
        "output_schema": {},
        "version": "1.0",
        "category": "chapter",
        "description": "Test template",
        "tags": ["writing"],
        "ab_test_group": "",
        "language": "de",
        "name": "Test Write Template",
        "is_active": True,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# from_queryset — basic happy path
# ---------------------------------------------------------------------------

class TestFromQueryset:
    def test_should_load_task_template_from_single_object(self):
        obj = _make_bfagent_obj()
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert tmpl.id == "test.task.write"
        assert tmpl.layer == TemplateLayer.TASK

    def test_should_split_system_prompt_into_system_layer(self):
        obj = _make_bfagent_obj()
        registry = DjangoTemplateRegistry.from_queryset([obj])
        system_tmpl = registry.get("test.task.write.system")
        assert system_tmpl.layer == TemplateLayer.SYSTEM
        assert "professional writer" in system_tmpl.template

    def test_should_set_system_template_cacheable(self):
        obj = _make_bfagent_obj()
        registry = DjangoTemplateRegistry.from_queryset([obj])
        system_tmpl = registry.get("test.task.write.system")
        assert system_tmpl.cacheable is True

    def test_should_not_create_system_template_when_system_prompt_empty(self):
        obj = _make_bfagent_obj(system_prompt="")
        registry = DjangoTemplateRegistry.from_queryset([obj])
        with pytest.raises(TemplateNotFoundError):
            registry.get("test.task.write.system")

    def test_should_not_create_system_template_when_system_prompt_none(self):
        obj = _make_bfagent_obj(system_prompt=None)
        registry = DjangoTemplateRegistry.from_queryset([obj])
        with pytest.raises(TemplateNotFoundError):
            registry.get("test.task.write.system")

    def test_should_skip_split_when_split_system_prompt_false(self):
        obj = _make_bfagent_obj()
        registry = DjangoTemplateRegistry.from_queryset([obj], split_system_prompt=False)
        with pytest.raises(TemplateNotFoundError):
            registry.get("test.task.write.system")
        # task template still created
        assert registry.get("test.task.write").layer == TemplateLayer.TASK

    def test_should_load_multiple_objects(self):
        objects = [
            _make_bfagent_obj(pk=1, template_key="writing.task.chapter"),
            _make_bfagent_obj(pk=2, template_key="writing.task.scene"),
        ]
        registry = DjangoTemplateRegistry.from_queryset(objects)
        assert registry.get("writing.task.chapter").id == "writing.task.chapter"
        assert registry.get("writing.task.scene").id == "writing.task.scene"

    def test_should_count_both_system_and_task_templates(self):
        obj = _make_bfagent_obj()
        registry = DjangoTemplateRegistry.from_queryset([obj])
        # 1 object → 2 templates (system + task)
        assert len(registry) == 2

    def test_should_use_empty_queryset_without_error(self):
        registry = DjangoTemplateRegistry.from_queryset([])
        assert len(registry) == 0


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------

class TestFieldMapping:
    def test_should_combine_required_and_optional_variables(self):
        obj = _make_bfagent_obj(
            required_variables=["topic", "genre"],
            optional_variables=["style", "tone"],
        )
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert set(tmpl.variables) == {"topic", "genre", "style", "tone"}

    def test_should_handle_none_variables(self):
        obj = _make_bfagent_obj(required_variables=None, optional_variables=None)
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert tmpl.variables == []

    def test_should_map_version_from_orm(self):
        obj = _make_bfagent_obj(version="2.3")
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert tmpl.version == "2.3"

    def test_should_map_output_schema_when_non_empty(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        obj = _make_bfagent_obj(output_schema=schema)
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert tmpl.output_schema == schema

    def test_should_set_output_schema_none_when_empty_dict(self):
        obj = _make_bfagent_obj(output_schema={})
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert tmpl.output_schema is None

    def test_should_map_category_to_phase(self):
        obj = _make_bfagent_obj(category="chapter")
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert tmpl.phase == "chapter"

    def test_should_store_metadata_with_description_and_tags(self):
        obj = _make_bfagent_obj(description="My template", tags=["writing", "ai"])
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert tmpl.metadata["description"] == "My template"
        assert tmpl.metadata["tags"] == ["writing", "ai"]

    def test_should_store_language_in_metadata(self):
        obj = _make_bfagent_obj(language="de")
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert tmpl.metadata["language"] == "de"


# ---------------------------------------------------------------------------
# output_format → response_format mapping
# ---------------------------------------------------------------------------

class TestOutputFormatMapping:
    def test_should_map_json_to_json_object(self):
        obj = _make_bfagent_obj(output_format="json")
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert tmpl.response_format == "json_object"

    def test_should_map_structured_to_json_schema(self):
        obj = _make_bfagent_obj(output_format="structured")
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert tmpl.response_format == "json_schema"

    def test_should_map_text_to_text(self):
        obj = _make_bfagent_obj(output_format="text")
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert tmpl.response_format == "text"

    def test_should_map_markdown_to_text(self):
        obj = _make_bfagent_obj(output_format="markdown")
        registry = DjangoTemplateRegistry.from_queryset([obj])
        tmpl = registry.get("test.task.write")
        assert tmpl.response_format == "text"

    def test_should_return_none_when_output_format_none(self):
        obj = _make_bfagent_obj(output_format=None)
        result = _bfagent_output_format_to_response_format(obj)
        assert result is None

    def test_should_default_unknown_format_to_text(self):
        obj = _make_bfagent_obj(output_format="csv")
        result = _bfagent_output_format_to_response_format(obj)
        assert result == "text"


# ---------------------------------------------------------------------------
# strict mode
# ---------------------------------------------------------------------------

class TestStrictMode:
    def test_should_raise_on_empty_template_key_in_strict_mode(self):
        obj = _make_bfagent_obj(template_key="")
        with pytest.raises(ValueError, match="resolved to empty value"):
            DjangoTemplateRegistry.from_queryset([obj], strict=True)

    def test_should_raise_on_empty_user_prompt_in_strict_mode(self):
        obj = _make_bfagent_obj(user_prompt_template="")
        with pytest.raises(ValueError, match="resolved to empty value"):
            DjangoTemplateRegistry.from_queryset([obj], strict=True)

    def test_should_skip_silently_in_non_strict_mode(self):
        obj = _make_bfagent_obj(template_key="")
        registry = DjangoTemplateRegistry.from_queryset([obj], strict=False)
        assert len(registry) == 0

    def test_should_raise_on_none_template_key_in_strict_mode(self):
        obj = _make_bfagent_obj(template_key=None)
        with pytest.raises(ValueError, match="resolved to empty value"):
            DjangoTemplateRegistry.from_queryset([obj], strict=True)


# ---------------------------------------------------------------------------
# Custom field_map
# ---------------------------------------------------------------------------

class TestCustomFieldMap:
    def test_should_accept_custom_field_map(self):
        """Custom field_map allows loading from non-standard model layouts."""
        custom_map = {
            "id": "slug",
            "template": "body",
            "layer": lambda obj: TemplateLayer.TASK,
        }
        obj = SimpleNamespace(slug="my.task.custom", body="Do something.", system_prompt=None)
        registry = DjangoTemplateRegistry.from_queryset([obj], field_map=custom_map)
        tmpl = registry.get("my.task.custom")
        assert tmpl.id == "my.task.custom"
        assert tmpl.template == "Do something."

    def test_should_work_with_callable_field_values(self):
        """All-callable field_map — maximum flexibility."""
        custom_map = {
            "id": lambda obj: f"custom.{obj.key}",
            "template": lambda obj: obj.content,
            "layer": lambda obj: TemplateLayer.TASK,
            "version": lambda obj: "3.0.0",
        }
        obj = SimpleNamespace(key="extract", content="Extract {{ data }}.", system_prompt=None)
        registry = DjangoTemplateRegistry.from_queryset([obj], field_map=custom_map)
        tmpl = registry.get("custom.extract")
        assert tmpl.version == "3.0.0"


# ---------------------------------------------------------------------------
# Integration: rendering with PromptRenderer
# ---------------------------------------------------------------------------

class TestIntegrationWithRenderer:
    def test_should_render_task_template_from_registry(self):
        from promptfw.renderer import PromptRenderer

        obj = _make_bfagent_obj(
            template_key="writing.task.chapter",
            user_prompt_template="Write about {{ topic }} in {{ genre }} style.",
            required_variables=["topic", "genre"],
            optional_variables=[],
            system_prompt="You are a novelist.",
        )
        registry = DjangoTemplateRegistry.from_queryset([obj])
        renderer = PromptRenderer()

        system_tmpl = registry.get("writing.task.chapter.system")
        task_tmpl = registry.get("writing.task.chapter")

        result = renderer.render_stack(
            [system_tmpl, task_tmpl],
            context={"topic": "dragons", "genre": "fantasy"},
        )
        assert "dragons" in result.user
        assert "fantasy" in result.user
        assert "novelist" in result.system

    def test_should_propagate_response_format_to_rendered_prompt(self):
        from promptfw.renderer import PromptRenderer

        obj = _make_bfagent_obj(
            template_key="lektorat.task.extract",
            user_prompt_template="Extract characters from: {{ text }}",
            required_variables=["text"],
            optional_variables=[],
            output_format="json",
            system_prompt="You are an analyst.",
        )
        registry = DjangoTemplateRegistry.from_queryset([obj])
        renderer = PromptRenderer()

        task_tmpl = registry.get("lektorat.task.extract")
        result = renderer.render_stack([task_tmpl], context={"text": "Alice walked in."})
        assert result.response_format == "json_object"


# ---------------------------------------------------------------------------
# _safe_repr
# ---------------------------------------------------------------------------

class TestSafeRepr:
    def test_should_include_class_name(self):
        obj = _make_bfagent_obj()
        r = _safe_repr(obj)
        assert "SimpleNamespace" in r

    def test_should_include_template_key(self):
        obj = _make_bfagent_obj(template_key="foo.bar")
        r = _safe_repr(obj)
        assert "foo.bar" in r

    def test_should_not_crash_on_broken_object(self):
        class Broken:
            @property
            def pk(self):
                raise RuntimeError("broken")
        r = _safe_repr(Broken())
        assert r  # just doesn't crash
