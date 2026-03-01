"""Tests for PromptStack.for_format() — issue #6."""

import pytest

from promptfw.exceptions import TemplateNotFoundError
from promptfw.schema import PromptTemplate, TemplateLayer
from promptfw.stack import PromptStack


def _tmpl(
    tid: str,
    layer: TemplateLayer,
    text: str = "hello",
    fmt: str | None = None,
) -> PromptTemplate:
    return PromptTemplate(
        id=tid, layer=layer, template=text, format_type=fmt, tokens_estimate=0
    )


class TestForFormat:
    def test_should_return_new_stack_instance(self):
        stack = PromptStack()
        stack.register(_tmpl("sys", TemplateLayer.SYSTEM, fmt=None))
        filtered = stack.for_format("roman")
        assert filtered is not stack

    def test_should_include_format_agnostic_templates(self):
        stack = PromptStack()
        stack.register(_tmpl("sys", TemplateLayer.SYSTEM, fmt=None))
        filtered = stack.for_format("roman")
        tmpl = filtered.registry.get("sys")
        assert tmpl.id == "sys"

    def test_should_include_matching_format_templates(self):
        stack = PromptStack()
        stack.register(_tmpl("task.roman", TemplateLayer.TASK, fmt="roman"))
        filtered = stack.for_format("roman")
        tmpl = filtered.registry.get("task.roman")
        assert tmpl.id == "task.roman"

    def test_should_exclude_other_format_templates(self):
        stack = PromptStack()
        stack.register(_tmpl("task.academic", TemplateLayer.TASK, fmt="academic"))
        filtered = stack.for_format("roman")
        with pytest.raises(TemplateNotFoundError):
            filtered.registry.get("task.academic")

    def test_should_keep_agnostic_and_filter_specific(self):
        stack = PromptStack()
        stack.register(_tmpl("sys", TemplateLayer.SYSTEM, fmt=None))
        stack.register(_tmpl("task.roman", TemplateLayer.TASK, fmt="roman"))
        stack.register(_tmpl("task.academic", TemplateLayer.TASK, fmt="academic"))

        filtered = stack.for_format("roman")
        assert len(filtered.registry) == 2
        filtered.registry.get("sys")
        filtered.registry.get("task.roman")
        with pytest.raises(TemplateNotFoundError):
            filtered.registry.get("task.academic")

    def test_should_be_chainable_with_render_stack(self):
        stack = PromptStack()
        stack.register(_tmpl("sys", TemplateLayer.SYSTEM, "SYSTEM", fmt=None))
        stack.register(_tmpl("task.roman", TemplateLayer.TASK, "ROMAN", fmt="roman"))
        stack.register(_tmpl("task.academic", TemplateLayer.TASK, "ACADEMIC", fmt="academic"))

        result = stack.for_format("roman").render_stack(["sys", "task.roman"], context={})
        assert result.system == "SYSTEM"
        assert result.user == "ROMAN"

    def test_should_share_renderer_with_parent(self):
        stack = PromptStack()
        filtered = stack.for_format("roman")
        assert filtered.renderer is stack.renderer
