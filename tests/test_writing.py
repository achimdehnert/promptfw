"""Tests for promptfw writing templates and get_writing_stack."""

import pytest

from promptfw.schema import TemplateLayer
from promptfw.stack import PromptStack
from promptfw.writing import WRITING_TEMPLATES, get_writing_stack


class TestWritingTemplates:
    def test_should_have_system_author_template(self):
        ids = {t.id for t in WRITING_TEMPLATES}
        assert "writing.system.author" in ids

    def test_should_have_system_editor_template(self):
        ids = {t.id for t in WRITING_TEMPLATES}
        assert "writing.system.editor" in ids

    def test_should_have_format_roman_template(self):
        ids = {t.id for t in WRITING_TEMPLATES}
        assert "writing.format.roman" in ids

    def test_should_have_format_nonfiction_template(self):
        ids = {t.id for t in WRITING_TEMPLATES}
        assert "writing.format.nonfiction" in ids

    def test_should_have_all_task_templates(self):
        task_ids = {t.id for t in WRITING_TEMPLATES if t.layer == TemplateLayer.TASK}
        expected = {
            "writing.task.write_chapter",
            "writing.task.write_scene",
            "writing.task.generate_outline",
            "writing.task.improve_prose",
            "writing.task.add_dialogue",
            "writing.task.summarize",
        }
        assert expected == task_ids

    def test_should_mark_system_templates_as_cacheable(self):
        for t in WRITING_TEMPLATES:
            if t.layer == TemplateLayer.SYSTEM:
                assert t.cacheable is True, f"{t.id} should be cacheable"

    def test_should_mark_format_templates_as_cacheable(self):
        for t in WRITING_TEMPLATES:
            if t.layer == TemplateLayer.FORMAT:
                assert t.cacheable is True, f"{t.id} should be cacheable"

    def test_should_mark_task_templates_as_not_cacheable(self):
        for t in WRITING_TEMPLATES:
            if t.layer == TemplateLayer.TASK:
                assert t.cacheable is False, f"{t.id} should not be cacheable"

    def test_should_follow_id_convention(self):
        for t in WRITING_TEMPLATES:
            parts = t.id.split(".")
            assert len(parts) == 3, f"Template id '{t.id}' must have 3 parts"
            assert parts[0] == "writing", f"Template id '{t.id}' must start with 'writing'"

    def test_should_set_phase_to_writing(self):
        for t in WRITING_TEMPLATES:
            assert t.phase == "writing", f"{t.id} should have phase='writing'"


class TestGetWritingStack:
    def test_should_return_promptstack(self):
        stack = get_writing_stack()
        assert isinstance(stack, PromptStack)

    def test_should_contain_all_templates(self):
        stack = get_writing_stack()
        for tmpl in WRITING_TEMPLATES:
            result = stack.registry.get(tmpl.id)
            assert result is not None, f"Template '{tmpl.id}' not found in stack"

    def test_should_return_independent_instances(self):
        stack1 = get_writing_stack()
        stack2 = get_writing_stack()
        assert stack1 is not stack2

    def test_should_render_write_chapter_task(self):
        stack = get_writing_stack()
        rendered = stack.render("writing.task.write_chapter", {
            "chapter_number": 3,
            "chapter_title": "Die Rückkehr",
            "chapter_outline": "Der Held kehrt zurück und findet sein Dorf verändert.",
            "target_words": 2500,
            "pov_character": "Elias",
            "mood": "melancholic",
            "genre": "Fantasy",
        })
        assert "3" in rendered.user
        assert "Die Rückkehr" in rendered.user
        assert "Elias" in rendered.user
        assert "2500" in rendered.user

    def test_should_render_write_chapter_with_optional_fields(self):
        stack = get_writing_stack()
        rendered = stack.render("writing.task.write_chapter", {
            "chapter_number": 1,
            "chapter_title": "Aufbruch",
            "chapter_outline": "Elias bricht auf.",
            "story_premise": "Ein Schmied entdeckt seine Kräfte.",
            "prior_chapter_summary": "Der Prolog endet mit einem Omen.",
        })
        assert "Ein Schmied" in rendered.user
        assert "Der Prolog" in rendered.user

    def test_should_render_system_author_into_system_prompt(self):
        stack = get_writing_stack()
        rendered = stack.render_stack(
            ["writing.system.author", "writing.task.write_chapter"],
            context={
                "chapter_number": 1,
                "chapter_title": "Test",
                "chapter_outline": "A short outline.",
            },
        )
        assert "Belletristik-Autor" in rendered.system
        assert rendered.user != ""

    def test_should_render_improve_prose_task(self):
        stack = get_writing_stack()
        rendered = stack.render("writing.task.improve_prose", {
            "original_text": "Er ging schnell. Es war dunkel.",
            "improvement_focus": "Rhythmus und Show-don't-tell",
        })
        assert "Er ging schnell" in rendered.user
        assert "Rhythmus" in rendered.user

    def test_should_render_summarize_task(self):
        stack = get_writing_stack()
        rendered = stack.render("writing.task.summarize", {
            "chapter_text": "Elias betrat die Stadt. Die Menschen sahen ihn misstrauisch an.",
        })
        assert "Elias betrat" in rendered.user

    def test_should_render_generate_outline_task(self):
        stack = get_writing_stack()
        rendered = stack.render("writing.task.generate_outline", {
            "chapter_number": 2,
        })
        assert "2" in rendered.user
        assert "Eröffnungsszene" in rendered.user

    def test_should_render_add_dialogue_task(self):
        stack = get_writing_stack()
        rendered = stack.render("writing.task.add_dialogue", {
            "characters": "Elias, Maria",
            "dialogue_purpose": "Verhandlung über das Schicksal des Dorfes",
            "context_text": "Sie standen sich gegenüber.",
        })
        assert "Elias, Maria" in rendered.user

    def test_should_render_write_scene_task(self):
        stack = get_writing_stack()
        rendered = stack.render("writing.task.write_scene", {
            "scene_description": "Elias betritt die Schmiede im Morgengrauen.",
            "characters": "Elias",
            "location": "Dorfschmiede",
            "mood": "hopeful",
        })
        assert "Elias" in rendered.user
        assert "Dorfschmiede" in rendered.user

    def test_should_render_full_stack_to_messages(self):
        stack = get_writing_stack()
        messages = stack.render_to_messages(
            ["writing.system.author", "writing.format.roman", "writing.task.write_chapter"],
            context={
                "chapter_number": 1,
                "chapter_title": "Aufbruch",
                "chapter_outline": "Elias bricht auf.",
                "genre": "Fantasy",
            },
        )
        roles = [m["role"] for m in messages]
        assert roles[0] == "system"
        assert roles[-1] == "user"
        assert "Belletristik-Autor" in messages[0]["content"]
        assert "Format-Vorgaben" in messages[0]["content"]
        assert "Aufbruch" in messages[-1]["content"]
