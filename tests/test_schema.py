"""Tests for promptfw schema dataclasses."""

from promptfw.schema import PromptTemplate, RenderedPrompt, TemplateLayer


def test_template_defaults():
    t = PromptTemplate(id="test", layer=TemplateLayer.TASK, template="Hello {{ name }}")
    assert t.variables == []
    assert t.version == "1.0.0"
    assert t.cacheable is False


def test_template_layer_values():
    assert TemplateLayer.SYSTEM == "system"
    assert TemplateLayer.TASK == "task"


def test_rendered_prompt_defaults():
    rp = RenderedPrompt(system="sys", user="usr")
    assert rp.estimated_tokens == 0
    assert rp.cache_breakpoints == []
