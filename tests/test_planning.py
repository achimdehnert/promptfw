"""Tests for promptfw planning templates and get_planning_stack."""

import pytest
from promptfw.planning import get_planning_stack, PLANNING_TEMPLATES
from promptfw.schema import TemplateLayer


class TestPlanningTemplates:
    def test_all_formats_have_task_template(self):
        formats = {"roman", "nonfiction", "academic", "scientific", "essay"}
        task_formats = {
            t.format_type for t in PLANNING_TEMPLATES if t.layer == TemplateLayer.TASK
        }
        assert formats == task_formats

    def test_all_formats_have_system_template(self):
        formats = {"roman", "nonfiction", "academic", "scientific", "essay"}
        system_formats = {
            t.format_type for t in PLANNING_TEMPLATES if t.layer == TemplateLayer.SYSTEM
        }
        assert formats == system_formats

    def test_template_ids_follow_convention(self):
        for tmpl in PLANNING_TEMPLATES:
            parts = tmpl.id.split(".")
            assert len(parts) == 3, f"Template id '{tmpl.id}' must have 3 parts"
            assert parts[2] == "planning"

    def test_system_templates_are_cacheable(self):
        for tmpl in PLANNING_TEMPLATES:
            if tmpl.layer == TemplateLayer.SYSTEM:
                assert tmpl.cacheable is True, f"{tmpl.id} system template should be cacheable"

    def test_academic_template_contains_research_question(self):
        tmpl = next(t for t in PLANNING_TEMPLATES if t.id == "academic.task.planning")
        assert "Forschungsfrage" in tmpl.template
        assert "Abstract" in tmpl.template
        assert "keywords" in tmpl.template.lower() or "Keywords" in tmpl.template

    def test_scientific_template_contains_imrad(self):
        tmpl = next(t for t in PLANNING_TEMPLATES if t.id == "scientific.task.planning")
        assert "IMRaD" in tmpl.template or "Hypothese" in tmpl.template

    def test_essay_template_contains_thesis(self):
        tmpl = next(t for t in PLANNING_TEMPLATES if t.id == "essay.task.planning")
        assert "These" in tmpl.template or "thesis" in tmpl.template.lower()

    def test_roman_template_contains_logline(self):
        tmpl = next(t for t in PLANNING_TEMPLATES if t.id == "roman.task.planning")
        assert "Logline" in tmpl.template or "logline" in tmpl.template


class TestGetPlanningStack:
    def test_returns_promptstack(self):
        from promptfw.stack import PromptStack
        stack = get_planning_stack()
        assert isinstance(stack, PromptStack)

    def test_stack_contains_all_templates(self):
        stack = get_planning_stack()
        for tmpl in PLANNING_TEMPLATES:
            result = stack.registry.get(tmpl.id)
            assert result is not None, f"Template '{tmpl.id}' not found in stack"

    def test_render_roman_planning(self):
        stack = get_planning_stack()
        rendered = stack.render("roman.task.planning", {
            "title": "Der letzte Magier",
            "genre": "Fantasy",
            "description": "Ein junger Schmied entdeckt seine magischen Kräfte.",
        })
        assert "Der letzte Magier" in rendered.user
        assert "Fantasy" in rendered.user

    def test_render_stack_roman_includes_system(self):
        stack = get_planning_stack()
        rendered = stack.render_stack(
            ["roman.system.planning", "roman.task.planning"],
            context={
                "title": "Der letzte Magier",
                "genre": "Fantasy",
                "description": "Ein junger Schmied entdeckt seine magischen Kräfte.",
            },
        )
        assert "Der letzte Magier" in rendered.user
        assert rendered.system != ""

    def test_render_academic_planning(self):
        stack = get_planning_stack()
        rendered = stack.render("academic.task.planning", {
            "title": "KI in der Medizin",
            "field_of_study": "Medizininformatik",
            "description": "Auswirkungen von LLMs auf die Diagnosestellung.",
            "citation_style": "APA",
        })
        assert "KI in der Medizin" in rendered.user
        assert "Medizininformatik" in rendered.user
        assert "APA" in rendered.user

    def test_render_scientific_planning(self):
        stack = get_planning_stack()
        rendered = stack.render("scientific.task.planning", {
            "title": "Wirksamkeit von X",
            "field_of_study": "Pharmakologie",
            "description": "Klinische Studie zur Wirksamkeit.",
            "citation_style": "Vancouver",
        })
        assert "Wirksamkeit von X" in rendered.user

    def test_render_essay_planning(self):
        stack = get_planning_stack()
        rendered = stack.render("essay.task.planning", {
            "title": "Über die Grenzen der KI",
            "description": "Ein Essay über ethische Grenzen.",
        })
        assert "Über die Grenzen der KI" in rendered.user

    def test_render_nonfiction_planning(self):
        stack = get_planning_stack()
        rendered = stack.render("nonfiction.task.planning", {
            "title": "Produktivität ohne Burnout",
            "description": "Praktische Strategien für nachhaltige Leistung.",
            "field_of_study": "Psychologie",
        })
        assert "Produktivität ohne Burnout" in rendered.user

    def test_multiple_stacks_are_independent(self):
        stack1 = get_planning_stack()
        stack2 = get_planning_stack()
        assert stack1 is not stack2
