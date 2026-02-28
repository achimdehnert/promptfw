"""Tests for TemplateRegistry."""

import pytest

from promptfw.exceptions import TemplateNotFoundError
from promptfw.registry import TemplateRegistry
from promptfw.schema import PromptTemplate, TemplateLayer


@pytest.fixture
def registry():
    r = TemplateRegistry()
    r.register(PromptTemplate(id="roman.draft.scene", layer=TemplateLayer.TASK, template="Write scene"))
    r.register(PromptTemplate(id="roman.draft.outline", layer=TemplateLayer.TASK, template="Write outline"))
    r.register(PromptTemplate(id="system.base", layer=TemplateLayer.SYSTEM, template="You are an AI"))
    return r


def test_get_exact(registry):
    t = registry.get("roman.draft.scene")
    assert t.id == "roman.draft.scene"


def test_get_wildcard(registry):
    t = registry.get("roman.*.scene")
    assert t.id == "roman.draft.scene"


def test_get_not_found(registry):
    with pytest.raises(TemplateNotFoundError) as exc:
        registry.get("nonexistent.template")
    assert "nonexistent.template" in str(exc.value)


def test_list_by_layer(registry):
    tasks = registry.list_by_layer(TemplateLayer.TASK)
    assert len(tasks) == 2
    systems = registry.list_by_layer(TemplateLayer.SYSTEM)
    assert len(systems) == 1


def test_register_overwrite(registry):
    registry.register(PromptTemplate(id="system.base", layer=TemplateLayer.SYSTEM, template="Updated"))
    assert registry.get("system.base").template == "Updated"


def test_len(registry):
    assert len(registry) == 3
