"""Tests for the PromptStack façade: for_format, render_with_fallback, from_file, hot-reload."""

import importlib.util

import pytest

from promptfw.exceptions import TemplateNotFoundError
from promptfw.schema import PromptTemplate, TemplateLayer
from promptfw.stack import PromptStack

_HAS_WATCHDOG = importlib.util.find_spec("watchdog") is not None


def _task(id_, template, format_type=None):
    return PromptTemplate(
        id=id_,
        layer=TemplateLayer.TASK,
        template=template,
        format_type=format_type,
    )


class TestForFormat:
    def test_should_keep_matching_and_format_agnostic_templates(self):
        stack = PromptStack()
        stack.register(_task("t.roman", "roman task", format_type="roman"))
        stack.register(_task("t.essay", "essay task", format_type="essay"))
        stack.register(_task("t.generic", "generic task", format_type=None))

        filtered = stack.for_format("roman")
        assert filtered.registry.get("t.roman") is not None
        assert filtered.registry.get("t.generic") is not None  # None is always included
        with pytest.raises(TemplateNotFoundError):
            filtered.registry.get("t.essay")

    def test_should_return_new_independent_stack(self):
        stack = PromptStack()
        stack.register(_task("t.roman", "x", format_type="roman"))
        assert stack.for_format("roman") is not stack


class TestRenderWithFallback:
    def test_should_render_first_matching_pattern(self):
        stack = PromptStack()
        stack.register(_task("writing.task.default", "Default body"))
        rendered = stack.render_with_fallback(
            ["writing.task.write_chapter.roman", "writing.task.default"],
            context={},
        )
        assert "Default body" in rendered.user

    def test_should_raise_when_no_pattern_matches(self):
        stack = PromptStack()
        with pytest.raises(TemplateNotFoundError):
            stack.render_with_fallback(["nope.a", "nope.b"], context={})


class TestFromFile:
    def test_should_raise_file_not_found_for_missing_path(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            PromptStack.from_file(tmp_path / "missing.yaml")

    def test_should_reject_jinja2_files_pointing_to_frontmatter(self, tmp_path):
        j2 = tmp_path / "tmpl.jinja2"
        j2.write_text("hello")
        with pytest.raises(ValueError, match="frontmatter"):
            PromptStack.from_file(j2)


class TestEnableHotReload:
    def test_should_delegate_to_registry(self, mocker):
        stack = PromptStack()
        spy = mocker.patch.object(stack.registry, "enable_hot_reload")
        stack.enable_hot_reload()
        spy.assert_called_once_with()

    @pytest.mark.skipif(
        _HAS_WATCHDOG, reason="watchdog installed; ImportError branch not exercised"
    )
    def test_should_raise_helpful_import_error_without_watchdog(self, tmp_path):
        stack = PromptStack.from_directory(tmp_path)
        with pytest.raises(ImportError, match="watchdog"):
            stack.enable_hot_reload()

    @pytest.mark.skipif(not _HAS_WATCHDOG, reason="requires watchdog")
    def test_should_start_observer_when_watchdog_available(self, tmp_path, mocker):
        observer = mocker.patch("watchdog.observers.Observer")
        stack = PromptStack.from_directory(tmp_path)
        stack.enable_hot_reload()
        observer.return_value.start.assert_called_once()
