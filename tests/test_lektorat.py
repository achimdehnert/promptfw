"""Tests for promptfw lektorat templates and get_lektorat_stack."""

import pytest

from promptfw.schema import TemplateLayer
from promptfw.stack import PromptStack
from promptfw.lektorat import LEKTORAT_TEMPLATES, get_lektorat_stack


class TestLektoratTemplates:
    def test_should_have_system_analyst_template(self):
        ids = {t.id for t in LEKTORAT_TEMPLATES}
        assert "lektorat.system.analyst" in ids

    def test_should_have_all_task_templates(self):
        task_ids = {t.id for t in LEKTORAT_TEMPLATES if t.layer == TemplateLayer.TASK}
        expected = {
            "lektorat.task.extract_characters",
            "lektorat.task.check_consistency",
            "lektorat.task.analyze_style",
            "lektorat.task.find_repetitions",
            "lektorat.task.check_timeline",
        }
        assert expected == task_ids

    def test_should_mark_system_template_as_cacheable(self):
        for t in LEKTORAT_TEMPLATES:
            if t.layer == TemplateLayer.SYSTEM:
                assert t.cacheable is True, f"{t.id} should be cacheable"

    def test_should_mark_task_templates_as_not_cacheable(self):
        for t in LEKTORAT_TEMPLATES:
            if t.layer == TemplateLayer.TASK:
                assert t.cacheable is False, f"{t.id} should not be cacheable"

    def test_should_follow_id_convention(self):
        for t in LEKTORAT_TEMPLATES:
            parts = t.id.split(".")
            assert len(parts) == 3, f"Template id '{t.id}' must have 3 parts"
            assert parts[0] == "lektorat", f"Template id '{t.id}' must start with 'lektorat'"

    def test_should_set_phase_to_lektorat(self):
        for t in LEKTORAT_TEMPLATES:
            assert t.phase == "lektorat", f"{t.id} should have phase='lektorat'"

    def test_should_set_json_response_format_on_task_templates(self):
        for t in LEKTORAT_TEMPLATES:
            if t.layer == TemplateLayer.TASK:
                assert t.response_format == "json_object", (
                    f"{t.id} should have response_format='json_object'"
                )

    def test_should_have_no_response_format_on_system_template(self):
        for t in LEKTORAT_TEMPLATES:
            if t.layer == TemplateLayer.SYSTEM:
                assert t.response_format is None


class TestGetLektoratStack:
    def test_should_return_promptstack(self):
        stack = get_lektorat_stack()
        assert isinstance(stack, PromptStack)

    def test_should_contain_all_templates(self):
        stack = get_lektorat_stack()
        for tmpl in LEKTORAT_TEMPLATES:
            result = stack.registry.get(tmpl.id)
            assert result is not None, f"Template '{tmpl.id}' not found in stack"

    def test_should_return_independent_instances(self):
        stack1 = get_lektorat_stack()
        stack2 = get_lektorat_stack()
        assert stack1 is not stack2

    def test_should_render_extract_characters_task(self):
        stack = get_lektorat_stack()
        rendered = stack.render("lektorat.task.extract_characters", {
            "content": "Elias betrat die Schmiede. Maria wartete bereits auf ihn.",
        })
        assert "Elias" in rendered.user
        assert "JSON-Array" in rendered.user

    def test_should_render_extract_characters_with_optional_chapter_number(self):
        stack = get_lektorat_stack()
        rendered = stack.render("lektorat.task.extract_characters", {
            "content": "Elias betrat die Schmiede.",
            "chapter_number": 3,
        })
        assert "3" in rendered.user

    def test_should_render_analyze_style_task(self):
        stack = get_lektorat_stack()
        rendered = stack.render("lektorat.task.analyze_style", {
            "text": "Er ging langsam durch die Gassen. Die Stille drückte auf ihn ein.",
        })
        assert "Er ging langsam" in rendered.user
        assert "JSON" in rendered.user

    def test_should_render_find_repetitions_task(self):
        stack = get_lektorat_stack()
        rendered = stack.render("lektorat.task.find_repetitions", {
            "text": "Er lief. Er lief schnell. Er lief immer schneller.",
        })
        assert "Er lief" in rendered.user

    def test_should_render_find_repetitions_with_threshold(self):
        stack = get_lektorat_stack()
        rendered = stack.render("lektorat.task.find_repetitions", {
            "text": "Testtext.",
            "threshold": 3,
        })
        assert "3" in rendered.user

    def test_should_render_check_timeline_task(self):
        stack = get_lektorat_stack()
        rendered = stack.render("lektorat.task.check_timeline", {
            "text": "Am Montag passierte X. Am Dienstag war schon Y passiert.",
        })
        assert "Montag" in rendered.user

    def test_should_render_check_timeline_with_optional_known_events(self):
        stack = get_lektorat_stack()
        rendered = stack.render("lektorat.task.check_timeline", {
            "text": "Am Montag passierte X.",
            "known_events": "Tag 1: Ankunft. Tag 2: Konflikt.",
        })
        assert "Ankunft" in rendered.user

    def test_should_render_system_analyst_into_system_prompt(self):
        stack = get_lektorat_stack()
        rendered = stack.render_stack(
            ["lektorat.system.analyst", "lektorat.task.extract_characters"],
            context={"content": "Elias stand am Fenster."},
        )
        assert "Literatur-Analyst" in rendered.system
        assert rendered.user != ""

    def test_should_propagate_response_format_to_rendered_prompt(self):
        stack = get_lektorat_stack()
        rendered = stack.render_stack(
            ["lektorat.system.analyst", "lektorat.task.extract_characters"],
            context={"content": "Elias stand am Fenster."},
        )
        assert rendered.response_format == "json_object"

    def test_should_have_no_response_format_when_only_system_rendered(self):
        stack = get_lektorat_stack()
        rendered = stack.render_stack(
            ["lektorat.system.analyst"],
            context={},
        )
        assert rendered.response_format is None

    def test_should_render_full_stack_to_messages(self):
        stack = get_lektorat_stack()
        messages = stack.render_to_messages(
            ["lektorat.system.analyst", "lektorat.task.analyze_style"],
            context={"text": "Er ging. Die Tür schloss sich."},
        )
        roles = [m["role"] for m in messages]
        assert roles[0] == "system"
        assert roles[-1] == "user"
        assert "Literatur-Analyst" in messages[0]["content"]
