"""
Tests for promptfw issues #2, #3, #7, #9.

#2  — context_scope sub-layers (CONTEXT_PROJECT / CONTEXT_CHAPTER / CONTEXT_SCENE)
#3  — render_with_fallback() in PromptStack
#7  — get_or_fallback() in TemplateRegistry
#9  — auto-calculate tokens_estimate via tiktoken
"""

import pytest

from promptfw.exceptions import TemplateNotFoundError
from promptfw.registry import TemplateRegistry
from promptfw.schema import PromptTemplate, TemplateLayer, USER_LAYERS
from promptfw.stack import PromptStack


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tmpl(tid: str, layer: TemplateLayer, text: str = "hello") -> PromptTemplate:
    return PromptTemplate(id=tid, layer=layer, template=text, tokens_estimate=0)


# ---------------------------------------------------------------------------
# Issue #7 — TemplateRegistry.get_or_fallback()
# ---------------------------------------------------------------------------

class TestGetOrFallback:
    def test_should_return_first_match(self):
        reg = TemplateRegistry()
        reg.register(_tmpl("writing.task.write_chapter", TemplateLayer.TASK))
        reg.register(_tmpl("writing.task.default", TemplateLayer.TASK))

        t = reg.get_or_fallback([
            "writing.task.write_chapter.roman",
            "writing.task.write_chapter",
            "writing.task.default",
        ])
        assert t.id == "writing.task.write_chapter"

    def test_should_skip_missing_and_use_fallback(self):
        reg = TemplateRegistry()
        reg.register(_tmpl("writing.task.default", TemplateLayer.TASK))

        t = reg.get_or_fallback([
            "writing.task.write_chapter.roman",
            "writing.task.write_chapter",
            "writing.task.default",
        ])
        assert t.id == "writing.task.default"

    def test_should_raise_when_all_missing(self):
        reg = TemplateRegistry()
        with pytest.raises(TemplateNotFoundError):
            reg.get_or_fallback(["a.b.c", "d.e.f"])

    def test_should_raise_on_empty_list(self):
        reg = TemplateRegistry()
        with pytest.raises((TemplateNotFoundError, ValueError)):
            reg.get_or_fallback([])

    def test_should_support_wildcard_patterns(self):
        reg = TemplateRegistry()
        reg.register(_tmpl("roman.draft.scene", TemplateLayer.TASK))

        t = reg.get_or_fallback(["roman.*.scene", "roman.draft.default"])
        assert t.id == "roman.draft.scene"


# ---------------------------------------------------------------------------
# Issue #9 — tokens_estimate auto-calculation
# ---------------------------------------------------------------------------

class TestTokensEstimate:
    def test_should_auto_calculate_when_zero_and_tiktoken_available(self):
        tmpl = PromptTemplate(
            id="test.task",
            layer=TemplateLayer.TASK,
            template="Write a short story about a blacksmith.",
            tokens_estimate=0,
        )
        try:
            import tiktoken  # noqa: F401
            assert tmpl.tokens_estimate > 0
        except ImportError:
            assert tmpl.tokens_estimate == 0

    def test_should_not_override_explicit_estimate(self):
        tmpl = PromptTemplate(
            id="test.task",
            layer=TemplateLayer.TASK,
            template="Write a short story about a blacksmith.",
            tokens_estimate=999,
        )
        assert tmpl.tokens_estimate == 999

    def test_should_remain_zero_for_empty_template(self):
        tmpl = PromptTemplate(
            id="test.task",
            layer=TemplateLayer.TASK,
            template="",
            tokens_estimate=0,
        )
        assert tmpl.tokens_estimate == 0


# ---------------------------------------------------------------------------
# Issue #3 — PromptStack.render_with_fallback()
# ---------------------------------------------------------------------------

class TestRenderWithFallback:
    def test_should_use_first_matching_fallback(self):
        stack = PromptStack()
        stack.register(_tmpl("writing.task.write_chapter", TemplateLayer.TASK, "chapter"))
        stack.register(_tmpl("writing.task.default", TemplateLayer.TASK, "default"))

        result = stack.render_with_fallback(
            ["writing.task.write_chapter.roman", "writing.task.write_chapter"],
            context={},
        )
        assert result.user == "chapter"

    def test_should_raise_if_all_fallbacks_missing(self):
        stack = PromptStack()
        with pytest.raises(TemplateNotFoundError):
            stack.render_with_fallback(["a.b.c", "d.e.f"], context={})

    def test_should_use_last_fallback_when_earlier_missing(self):
        stack = PromptStack()
        stack.register(_tmpl("writing.task.default", TemplateLayer.TASK, "fallback"))

        result = stack.render_with_fallback(
            ["writing.task.specific", "writing.task.default"],
            context={},
        )
        assert result.user == "fallback"


# ---------------------------------------------------------------------------
# Issue #2 — context_scope sub-layers
# ---------------------------------------------------------------------------

class TestContextSubLayers:
    def test_should_have_new_sub_layers_in_enum(self):
        assert TemplateLayer.CONTEXT_PROJECT.value == "context_project"
        assert TemplateLayer.CONTEXT_CHAPTER.value == "context_chapter"
        assert TemplateLayer.CONTEXT_SCENE.value == "context_scene"

    def test_should_include_sub_layers_in_user_layers(self):
        assert TemplateLayer.CONTEXT_PROJECT in USER_LAYERS
        assert TemplateLayer.CONTEXT_CHAPTER in USER_LAYERS
        assert TemplateLayer.CONTEXT_SCENE in USER_LAYERS

    def test_should_render_context_sublayers_in_order(self):
        stack = PromptStack()
        stack.register(_tmpl("sys", TemplateLayer.SYSTEM, "SYSTEM"))
        stack.register(_tmpl("proj", TemplateLayer.CONTEXT_PROJECT, "PROJECT"))
        stack.register(_tmpl("chap", TemplateLayer.CONTEXT_CHAPTER, "CHAPTER"))
        stack.register(_tmpl("scene", TemplateLayer.CONTEXT_SCENE, "SCENE"))
        stack.register(_tmpl("task", TemplateLayer.TASK, "TASK"))

        result = stack.render_stack(
            ["sys", "scene", "chap", "proj", "task"],  # intentionally shuffled
            context={},
        )
        user = result.user
        proj_pos = user.index("PROJECT")
        chap_pos = user.index("CHAPTER")
        scene_pos = user.index("SCENE")
        task_pos = user.index("TASK")

        assert proj_pos < chap_pos < scene_pos < task_pos

    def test_should_keep_existing_context_layer_working(self):
        stack = PromptStack()
        stack.register(_tmpl("ctx", TemplateLayer.CONTEXT, "CONTEXT"))
        stack.register(_tmpl("task", TemplateLayer.TASK, "TASK"))

        result = stack.render_stack(["ctx", "task"], context={})
        assert "CONTEXT" in result.user
        assert "TASK" in result.user

    def test_should_parse_sub_layer_from_string(self):
        layer = TemplateLayer("context_project")
        assert layer == TemplateLayer.CONTEXT_PROJECT
