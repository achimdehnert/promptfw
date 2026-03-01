"""Tests for promptfw schema dataclasses."""

from promptfw.schema import PromptTemplate, RenderedPrompt, TemplateLayer


def test_should_set_default_values_on_prompt_template():
    t = PromptTemplate(id="test", layer=TemplateLayer.TASK, template="Hello {{ name }}")
    assert t.variables == []
    assert t.version == "1.0.0"
    assert t.cacheable is False


def test_should_have_correct_string_values_for_template_layers():
    assert TemplateLayer.SYSTEM == "system"
    assert TemplateLayer.TASK == "task"


def test_should_set_default_values_on_rendered_prompt():
    rp = RenderedPrompt(system="sys", user="usr")
    assert rp.estimated_tokens == 0
    assert rp.cache_breakpoints == []
