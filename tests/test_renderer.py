"""Tests for PromptRenderer."""

import pytest

from promptfw.exceptions import TemplateRenderError
from promptfw.renderer import PromptRenderer
from promptfw.schema import PromptTemplate, TemplateLayer


@pytest.fixture
def renderer():
    return PromptRenderer()


def test_render_single_template(renderer):
    t = PromptTemplate(id="t1", layer=TemplateLayer.TASK, template="Hello {{ name }}!")
    result = renderer.render_stack([t], {"name": "Alice"})
    assert "Alice" in result.user
    assert result.system == ""


def test_render_system_template(renderer):
    t = PromptTemplate(id="s1", layer=TemplateLayer.SYSTEM, template="You are {{ role }}.")
    result = renderer.render_stack([t], {"role": "an assistant"})
    assert "an assistant" in result.system
    assert result.user == ""


def test_render_stack_combined(renderer):
    templates = [
        PromptTemplate(id="s1", layer=TemplateLayer.SYSTEM, template="You are {{ role }}."),
        PromptTemplate(id="f1", layer=TemplateLayer.FORMAT, template="Use {{ style }} style."),
        PromptTemplate(id="t1", layer=TemplateLayer.TASK, template="Write about {{ topic }}."),
    ]
    result = renderer.render_stack(templates, {"role": "author", "style": "formal", "topic": "dragons"})
    assert "author" in result.system
    assert "formal" in result.system
    assert "dragons" in result.user


def test_render_missing_variable_raises(renderer):
    t = PromptTemplate(id="t1", layer=TemplateLayer.TASK, template="Hello {{ name }}!")
    with pytest.raises(TemplateRenderError) as exc:
        renderer.render_stack([t], {})
    assert "t1" in str(exc.value)
    assert "name" in str(exc.value)


def test_render_empty_template_skipped(renderer):
    templates = [
        PromptTemplate(id="s1", layer=TemplateLayer.SYSTEM, template="   "),
        PromptTemplate(id="t1", layer=TemplateLayer.TASK, template="Hello!"),
    ]
    result = renderer.render_stack(templates, {})
    assert result.system == ""
    assert "Hello!" in result.user


def test_estimated_tokens_nonzero(renderer):
    t = PromptTemplate(id="t1", layer=TemplateLayer.TASK,
                       template="Write a long story about dragons and wizards.")
    result = renderer.render_stack([t], {})
    assert result.estimated_tokens > 0
