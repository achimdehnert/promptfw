"""
Regression tests for ADR review fixes.

Befund #5:  strict-Mode in TemplateRegistry.from_directory()
Befund #6:  response_format-Validierung beim YAML-Load
Befund #9:  LLMResponseError statt TemplateRenderError in parsing.py
Befund #10: output_schema/response_format nur von TASK-Layer propagiert
"""

import pytest

from promptfw.exceptions import LLMResponseError, TemplateRenderError
from promptfw.schema import VALID_RESPONSE_FORMATS, PromptTemplate, RenderedPrompt, TemplateLayer
from promptfw.registry import TemplateRegistry
from promptfw.renderer import PromptRenderer


# ---------------------------------------------------------------------------
# Befund #9 — LLMResponseError ist separater Exception-Typ
# ---------------------------------------------------------------------------

class TestLLMResponseError:
    def test_should_not_be_instance_of_template_render_error(self):
        err = LLMResponseError(cause="no json found", preview="plain text")
        assert not isinstance(err, TemplateRenderError)

    def test_should_contain_cause_in_message(self):
        err = LLMResponseError(cause="no json found")
        assert "no json found" in str(err)

    def test_should_contain_preview_in_message_when_provided(self):
        err = LLMResponseError(cause="no json found", preview="plain text here")
        assert "plain text here" in str(err)

    def test_should_not_be_caught_by_template_render_error_handler(self):
        from promptfw.parsing import extract_json_strict
        caught_as_render_error = False
        caught_as_llm_error = False
        try:
            extract_json_strict("no json here")
        except TemplateRenderError:
            caught_as_render_error = True
        except LLMResponseError:
            caught_as_llm_error = True
        assert not caught_as_render_error
        assert caught_as_llm_error


# ---------------------------------------------------------------------------
# Befund #10 — output_schema/response_format nur von TASK-Layer propagiert
# ---------------------------------------------------------------------------

class TestResponseFormatPropagation:
    def _make_renderer(self):
        return PromptRenderer()

    def test_should_propagate_response_format_from_task_template(self):
        renderer = self._make_renderer()
        templates = [
            PromptTemplate(
                id="t.system.base", layer=TemplateLayer.SYSTEM,
                template="You are an analyst.", cacheable=True,
            ),
            PromptTemplate(
                id="t.task.extract", layer=TemplateLayer.TASK,
                template="Extract data from: {{ text }}",
                variables=["text"],
                response_format="json_object",
            ),
        ]
        result = renderer.render_stack(templates, {"text": "sample"})
        assert result.response_format == "json_object"

    def test_should_not_propagate_response_format_from_system_template(self):
        renderer = self._make_renderer()
        templates = [
            PromptTemplate(
                id="t.system.base", layer=TemplateLayer.SYSTEM,
                template="You are an analyst.",
                cacheable=True,
                response_format="json_object",  # should be ignored
            ),
            PromptTemplate(
                id="t.task.plain", layer=TemplateLayer.TASK,
                template="Do something.",
                # no response_format
            ),
        ]
        result = renderer.render_stack(templates, {})
        assert result.response_format is None

    def test_should_not_propagate_response_format_from_format_template(self):
        renderer = self._make_renderer()
        templates = [
            PromptTemplate(
                id="t.format.roman", layer=TemplateLayer.FORMAT,
                template="Format rules.",
                cacheable=True,
                response_format="json_schema",  # should be ignored
            ),
            PromptTemplate(
                id="t.task.write", layer=TemplateLayer.TASK,
                template="Write something.",
            ),
        ]
        result = renderer.render_stack(templates, {})
        assert result.response_format is None

    def test_should_propagate_output_schema_from_task_template(self):
        renderer = self._make_renderer()
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        templates = [
            PromptTemplate(
                id="t.task.extract", layer=TemplateLayer.TASK,
                template="Extract.",
                output_schema=schema,
                response_format="json_schema",
            ),
        ]
        result = renderer.render_stack(templates, {})
        assert result.output_schema == schema

    def test_last_task_template_wins_for_response_format(self):
        renderer = self._make_renderer()
        templates = [
            PromptTemplate(
                id="t.task.first", layer=TemplateLayer.TASK,
                template="First.",
                response_format="json_object",
            ),
            PromptTemplate(
                id="t.task.second", layer=TemplateLayer.TASK,
                template="Second.",
                response_format="text",
            ),
        ]
        result = renderer.render_stack(templates, {})
        assert result.response_format == "text"


# ---------------------------------------------------------------------------
# Befund #5 — strict-Mode in TemplateRegistry
# ---------------------------------------------------------------------------

class TestRegistryStrictMode:
    def test_should_raise_on_missing_required_fields_in_strict_mode(self, tmp_path):
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("id: test.task.missing\nlayer: task\n")  # missing: template
        with pytest.raises(ValueError, match="missing required fields"):
            TemplateRegistry.from_directory(tmp_path, strict=True)

    def test_should_raise_on_invalid_layer_in_strict_mode(self, tmp_path):
        bad_yaml = tmp_path / "bad_layer.yaml"
        bad_yaml.write_text(
            "id: test.task.bad\nlayer: nonexistent\ntemplate: Hello\n"
        )
        with pytest.raises(ValueError, match="invalid layer"):
            TemplateRegistry.from_directory(tmp_path, strict=True)

    def test_should_raise_on_invalid_response_format_in_strict_mode(self, tmp_path):
        bad_yaml = tmp_path / "bad_rf.yaml"
        bad_yaml.write_text(
            "id: test.task.bad\nlayer: task\ntemplate: Hi\nresponse_format: json_objekt\n"
        )
        with pytest.raises(ValueError, match="invalid response_format"):
            TemplateRegistry.from_directory(tmp_path, strict=True)

    def test_should_skip_silently_in_non_strict_mode(self, tmp_path):
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("id: test.task.missing\nlayer: task\n")  # missing: template
        # no exception — just logs warning and skips
        registry = TemplateRegistry.from_directory(tmp_path, strict=False)
        assert len(registry) == 0

    def test_should_load_valid_template_in_strict_mode(self, tmp_path):
        good_yaml = tmp_path / "good.yaml"
        good_yaml.write_text(
            "id: test.task.good\nlayer: task\ntemplate: Hello {{ name }}\n"
        )
        registry = TemplateRegistry.from_directory(tmp_path, strict=True)
        assert len(registry) == 1
        assert registry.get("test.task.good").id == "test.task.good"

    def test_should_validate_response_format_value(self, tmp_path):
        good_yaml = tmp_path / "good_rf.yaml"
        good_yaml.write_text(
            "id: test.task.rf\nlayer: task\ntemplate: Hi\nresponse_format: json_object\n"
        )
        registry = TemplateRegistry.from_directory(tmp_path, strict=True)
        assert registry.get("test.task.rf").response_format == "json_object"


# ---------------------------------------------------------------------------
# Befund #6 — VALID_RESPONSE_FORMATS Konstante
# ---------------------------------------------------------------------------

class TestValidResponseFormats:
    def test_should_contain_json_object(self):
        assert "json_object" in VALID_RESPONSE_FORMATS

    def test_should_contain_json_schema(self):
        assert "json_schema" in VALID_RESPONSE_FORMATS

    def test_should_contain_text(self):
        assert "text" in VALID_RESPONSE_FORMATS

    def test_should_not_contain_invalid_values(self):
        assert "json_objekt" not in VALID_RESPONSE_FORMATS
        assert "JSON" not in VALID_RESPONSE_FORMATS
        assert "" not in VALID_RESPONSE_FORMATS
