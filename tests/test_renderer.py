"""Tests for PromptRenderer."""

import pytest

from promptfw.exceptions import TemplateRenderError
from promptfw.renderer import PromptRenderer
from promptfw.schema import PromptTemplate, TemplateLayer


@pytest.fixture
def renderer():
    return PromptRenderer()


def test_should_render_task_template_into_user_prompt(renderer):
    t = PromptTemplate(id="t1", layer=TemplateLayer.TASK, template="Hello {{ name }}!")
    result = renderer.render_stack([t], {"name": "Alice"})
    assert "Alice" in result.user
    assert result.system == ""


def test_should_render_system_template_into_system_prompt(renderer):
    t = PromptTemplate(id="s1", layer=TemplateLayer.SYSTEM, template="You are {{ role }}.")
    result = renderer.render_stack([t], {"role": "an assistant"})
    assert "an assistant" in result.system
    assert result.user == ""


def test_should_combine_system_and_format_into_system_user_into_user(renderer):
    templates = [
        PromptTemplate(id="s1", layer=TemplateLayer.SYSTEM, template="You are {{ role }}."),
        PromptTemplate(id="f1", layer=TemplateLayer.FORMAT, template="Use {{ style }} style."),
        PromptTemplate(id="t1", layer=TemplateLayer.TASK, template="Write about {{ topic }}."),
    ]
    result = renderer.render_stack(templates, {"role": "author", "style": "formal", "topic": "dragons"})
    assert "author" in result.system
    assert "formal" in result.system
    assert "dragons" in result.user


def test_should_raise_render_error_on_missing_variable(renderer):
    t = PromptTemplate(id="t1", layer=TemplateLayer.TASK, template="Hello {{ name }}!")
    with pytest.raises(TemplateRenderError) as exc:
        renderer.render_stack([t], {})
    assert "t1" in str(exc.value)
    assert "name" in str(exc.value)


def test_should_skip_whitespace_only_templates(renderer):
    templates = [
        PromptTemplate(id="s1", layer=TemplateLayer.SYSTEM, template="   "),
        PromptTemplate(id="t1", layer=TemplateLayer.TASK, template="Hello!"),
    ]
    result = renderer.render_stack(templates, {})
    assert result.system == ""
    assert "Hello!" in result.user


def test_should_estimate_nonzero_tokens_for_nonempty_template(renderer):
    t = PromptTemplate(id="t1", layer=TemplateLayer.TASK,
                       template="Write a long story about dragons and wizards.")
    result = renderer.render_stack([t], {})
    assert result.estimated_tokens > 0


def test_should_render_to_messages_with_system_and_user(renderer):
    templates = [
        PromptTemplate(id="s1", layer=TemplateLayer.SYSTEM, template="You are {{ role }}."),
        PromptTemplate(id="t1", layer=TemplateLayer.TASK, template="Write about {{ topic }}."),
    ]
    messages = renderer.render_to_messages(templates, {"role": "author", "topic": "dragons"})
    assert messages[0] == {"role": "system", "content": "You are author."}
    assert messages[-1] == {"role": "user", "content": "Write about dragons."}


def test_should_interleave_few_shot_messages_between_system_and_user(renderer):
    few_shot_tmpl = PromptTemplate(
        id="fs1",
        layer=TemplateLayer.FEW_SHOT,
        template="",
        few_shot_examples=[
            {"user": "Input A", "assistant": "Output A"},
            {"user": "Input B", "assistant": "Output B"},
        ],
    )
    task_tmpl = PromptTemplate(id="t1", layer=TemplateLayer.TASK, template="Now do {{ task }}.")
    messages = renderer.render_to_messages([few_shot_tmpl, task_tmpl], {"task": "this"})
    roles = [m["role"] for m in messages]
    assert roles == ["user", "assistant", "user", "assistant", "user"]
    assert messages[0]["content"] == "Input A"
    assert messages[1]["content"] == "Output A"
    assert messages[-1]["content"] == "Now do this."


def test_should_store_few_shot_messages_on_rendered_prompt(renderer):
    few_shot_tmpl = PromptTemplate(
        id="fs1",
        layer=TemplateLayer.FEW_SHOT,
        template="",
        few_shot_examples=[{"user": "Q", "assistant": "A"}],
    )
    result = renderer.render_stack([few_shot_tmpl], {})
    assert len(result.few_shot_messages) == 2
    assert result.few_shot_messages[0] == {"role": "user", "content": "Q"}
    assert result.few_shot_messages[1] == {"role": "assistant", "content": "A"}
