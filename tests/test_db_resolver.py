"""Tests for promptfw.db_resolver.DBPromptResolver (Django-free DB prompt resolution)."""

import pytest

from promptfw.db_resolver import _GENERIC_SYSTEM, DBPromptResolver
from promptfw.planning import get_planning_stack


@pytest.fixture
def resolver():
    return DBPromptResolver(get_planning_stack())


class TestLoadConfig:
    def test_should_normalize_config_from_loader(self, resolver):
        def loader(slug):
            return {
                "action_code": "planning_screenplay",
                "template_prefix": "screenplay",
                "system_prompt": "You are a screenwriter.",
                "user_template": "Write {title}.",
            }

        cfg = resolver.load_config("screenplay", loader)
        assert cfg["action_code"] == "planning_screenplay"
        assert cfg["template_prefix"] == "screenplay"
        assert cfg["system_prompt"] == "You are a screenwriter."

    def test_should_fall_back_to_slug_when_prefix_missing(self, resolver):
        cfg = resolver.load_config(
            "mytale", lambda slug: {"action_code": "", "template_prefix": ""}
        )
        # empty template_prefix falls back to the slug, not the default prefix
        assert cfg["template_prefix"] == "mytale"
        assert cfg["action_code"] == "planning_novel"  # default_action_code

    def test_should_use_defaults_when_loader_returns_none(self, resolver):
        cfg = resolver.load_config("unknown", lambda slug: None)
        assert cfg["action_code"] == "planning_novel"
        assert cfg["template_prefix"] == "roman"
        assert cfg["system_prompt"] == ""

    def test_should_not_raise_when_loader_raises(self, resolver):
        def broken_loader(slug):
            raise RuntimeError("db down")

        cfg = resolver.load_config("x", broken_loader)  # must never propagate
        assert cfg["template_prefix"] == "roman"


class TestBuildMessages:
    def test_should_use_db_custom_prompts_when_both_set(self, resolver):
        cfg = {
            "action_code": "planning_novel",
            "template_prefix": "roman",
            "system_prompt": "SYS",
            "user_template": "Book: {title}",
        }
        messages = resolver.build_messages(cfg, {"title": "Dune"})
        assert messages == [
            {"role": "system", "content": "SYS"},
            {"role": "user", "content": "Book: Dune"},
        ]

    def test_should_keep_raw_user_template_on_missing_format_key(self, resolver):
        cfg = {
            "action_code": "planning_novel",
            "template_prefix": "roman",
            "system_prompt": "SYS",
            "user_template": "Book: {missing}",
        }
        # KeyError on .format(**context) must not crash — raw template kept
        messages = resolver.build_messages(cfg, {"title": "Dune"})
        assert messages[1]["content"] == "Book: {missing}"

    def test_should_render_promptfw_stack_when_no_db_custom(self, resolver):
        cfg = {
            "action_code": "planning_novel",
            "template_prefix": "roman",
            "system_prompt": "",
            "user_template": "",
        }
        messages = resolver.build_messages(
            cfg,
            {"title": "Der letzte Magier", "genre": "Fantasy", "description": "..."},
        )
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "Der letzte Magier" in messages[1]["content"]

    def test_should_fall_back_to_generic_on_unknown_prefix(self, resolver):
        cfg = {
            "action_code": "planning_novel",
            "template_prefix": "does-not-exist",
            "system_prompt": "",
            "user_template": "",
        }
        messages = resolver.build_messages(cfg, {"description": "A short brief."})
        assert messages[0]["content"] == _GENERIC_SYSTEM
        assert "A short brief." in messages[1]["content"]


class TestResolve:
    def test_should_return_action_code_and_messages(self, resolver):
        action_code, messages = resolver.resolve(
            "screenplay",
            lambda slug: {
                "action_code": "planning_screenplay",
                "template_prefix": "screenplay",
                "system_prompt": "SYS",
                "user_template": "Title: {title}",
            },
            {"title": "Heat"},
        )
        assert action_code == "planning_screenplay"
        assert messages[1]["content"] == "Title: Heat"
