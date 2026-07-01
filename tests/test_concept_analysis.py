"""Tests for promptfw concept-analysis templates and get_concept_analysis_stack."""

from promptfw.concept_analysis import (
    CONCEPT_ANALYSIS_TEMPLATES,
    get_concept_analysis_stack,
)
from promptfw.schema import TemplateLayer
from promptfw.stack import PromptStack


class TestConceptAnalysisTemplates:
    def test_should_expose_all_six_templates(self):
        assert len(CONCEPT_ANALYSIS_TEMPLATES) == 6

    def test_should_use_three_part_ids_prefixed_concept(self):
        for tmpl in CONCEPT_ANALYSIS_TEMPLATES:
            parts = tmpl.id.split(".")
            assert len(parts) == 3, f"Template id '{tmpl.id}' must have 3 parts"
            assert parts[0] == "concept"
            assert parts[1] in {"system", "task"}

    def test_should_mark_system_templates_cacheable(self):
        for tmpl in CONCEPT_ANALYSIS_TEMPLATES:
            if tmpl.layer == TemplateLayer.SYSTEM:
                assert tmpl.cacheable is True, f"{tmpl.id} system template should be cacheable"

    def test_should_mark_task_templates_not_cacheable(self):
        for tmpl in CONCEPT_ANALYSIS_TEMPLATES:
            if tmpl.layer == TemplateLayer.TASK:
                assert tmpl.cacheable is False, f"{tmpl.id} task template should not be cacheable"

    def test_should_have_analyst_and_structure_templates(self):
        ids = {t.id for t in CONCEPT_ANALYSIS_TEMPLATES}
        assert "concept.system.analyst" in ids
        assert "concept.task.analyze_structure" in ids


class TestGetConceptAnalysisStack:
    def test_should_return_promptstack(self):
        assert isinstance(get_concept_analysis_stack(), PromptStack)

    def test_should_register_all_templates(self):
        stack = get_concept_analysis_stack()
        for tmpl in CONCEPT_ANALYSIS_TEMPLATES:
            assert stack.registry.get(tmpl.id) is not None, f"{tmpl.id} not registered"

    def test_should_render_analyst_system_in_german_by_default(self):
        stack = get_concept_analysis_stack()
        rendered = stack.render(
            "concept.system.analyst",
            {"scopes": "Brandschutz, Explosionsschutz", "language": "de"},
        )
        assert "Antworte immer auf Deutsch" in rendered.system
        assert "Brandschutz" in rendered.system

    def test_should_render_analyst_system_in_english_when_language_en(self):
        stack = get_concept_analysis_stack()
        rendered = stack.render(
            "concept.system.analyst",
            {"scopes": "fire safety", "language": "en"},
        )
        assert "Always respond in English" in rendered.system

    def test_should_render_structure_task_with_document_fields(self):
        stack = get_concept_analysis_stack()
        rendered = stack.render(
            "concept.task.analyze_structure",
            {
                "scope": "explosionsschutz",
                "title": "Ex-Schutz Dokument 2024",
                "page_count": 12,
                "text": "Extrahierter Beispieltext.",
            },
        )
        assert "Ex-Schutz Dokument 2024" in rendered.user
        assert "explosionsschutz" in rendered.user
        assert "Extrahierter Beispieltext." in rendered.user

    def test_should_render_full_analysis_stack_with_system_and_user(self):
        stack = get_concept_analysis_stack()
        rendered = stack.render_stack(
            ["concept.system.analyst", "concept.task.analyze_structure"],
            context={
                "scopes": "Brandschutz",
                "language": "de",
                "scope": "brandschutz",
                "title": "Konzept A",
                "page_count": 5,
                "text": "...",
            },
        )
        assert rendered.system != ""
        assert "Konzept A" in rendered.user

    def test_should_return_independent_stacks(self):
        assert get_concept_analysis_stack() is not get_concept_analysis_stack()
