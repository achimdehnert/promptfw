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


def test_should_convert_to_messages_with_system_and_user():
    rp = RenderedPrompt(system="You are helpful.", user="Hello!")
    assert rp.to_messages() == [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello!"},
    ]


def test_should_convert_to_messages_with_few_shot():
    few_shot = [
        {"role": "user", "content": "Example Q"},
        {"role": "assistant", "content": "Example A"},
    ]
    rp = RenderedPrompt(system="sys", user="real Q", few_shot_messages=few_shot)
    assert rp.to_messages() == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "Example Q"},
        {"role": "assistant", "content": "Example A"},
        {"role": "user", "content": "real Q"},
    ]


def test_should_omit_empty_system_from_messages():
    rp = RenderedPrompt(system="", user="Hello!")
    assert rp.to_messages() == [{"role": "user", "content": "Hello!"}]
