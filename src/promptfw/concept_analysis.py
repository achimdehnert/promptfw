"""
Built-in concept-analysis prompt templates for document structure extraction.

Covers document structure analysis, template merging, and field prefill.
Used by iil-concept-templates package (ADR-147).

Key design: scopes and language are Jinja2 context variables, NOT hardcoded.
Consumers pass ``scopes`` (comma-separated list) and ``language`` at render time.

Usage::

    from promptfw import get_concept_analysis_stack

    stack = get_concept_analysis_stack()
    rendered = stack.render_stack(
        ["concept.system.analyst", "concept.task.analyze_structure"],
        context={
            "scopes": "Brandschutz, Explosionsschutz, Ausschreibungen",
            "language": "de",
            "scope": "explosionsschutz",
            "title": "Ex-Schutz Dokument 2024",
            "page_count": 12,
            "text": "Extrahierter Text...",
        },
    )
"""

from __future__ import annotations

from promptfw.schema import PromptTemplate, TemplateLayer
from promptfw.stack import PromptStack

# Language instruction lookup — used in Jinja2 templates
_LANG_MAP = {
    "de": "Antworte immer auf Deutsch.",
    "en": "Always respond in English.",
}

CONCEPT_ANALYSIS_TEMPLATES: list[PromptTemplate] = [
    # =========================================================================
    # SYSTEM — stable, cacheable
    # =========================================================================
    PromptTemplate(
        id="concept.system.analyst",
        layer=TemplateLayer.SYSTEM,
        cacheable=True,
        phase="analysis",
        response_format="json_object",
        template=(
            "Du bist ein Experte für die Strukturanalyse von technischen "
            "Konzeptdokumenten ({{ scopes|default('technische Fachkonzepte') }}).\n"
            "Du analysierst den extrahierten Text eines Dokuments und "
            "identifizierst die Kapitelstruktur, Pflichtabschnitte und "
            "Formularfelder.\n"
            "{% if language == 'en' %}Always respond in English."
            "{% else %}Antworte immer auf Deutsch.{% endif %} "
            "Strukturiere deine Antwort ausschließlich als JSON."
        ),
        variables=["scopes", "language"],
    ),
    PromptTemplate(
        id="concept.system.merger",
        layer=TemplateLayer.SYSTEM,
        cacheable=True,
        phase="analysis",
        response_format="json_object",
        template=(
            "Du bist ein Experte für die Zusammenführung von "
            "Dokumentvorlagen.\n"
            "Du erhältst mehrere analysierte Konzept-Strukturen und erstellst "
            "daraus ein konsolidiertes Master-Template mit den häufigsten "
            "Abschnitten und Feldern.\n"
            "{% if language == 'en' %}Always respond in English."
            "{% else %}Antworte immer auf Deutsch.{% endif %} "
            "Strukturiere deine Antwort ausschließlich als JSON."
        ),
        variables=["language"],
    ),
    PromptTemplate(
        id="concept.system.prefill",
        layer=TemplateLayer.SYSTEM,
        cacheable=True,
        phase="prefill",
        template=(
            "Du bist ein Fachexperte für {{ scope|default('technische Konzepte') }}.\n"
            "Du hilfst beim Ausfüllen von Formularfeldern in strukturierten "
            "Konzeptdokumenten.\n"
            "{% if language == 'en' %}Always respond in English."
            "{% else %}Antworte immer auf Deutsch.{% endif %}\n"
            "Antworte NUR mit dem Feldwert — keine Erklärungen, "
            "keine Formatierung, kein Markdown."
        ),
        variables=["scope", "language"],
    ),
    # =========================================================================
    # TASK — dynamic, not cacheable
    # =========================================================================
    PromptTemplate(
        id="concept.task.analyze_structure",
        layer=TemplateLayer.TASK,
        cacheable=False,
        phase="analysis",
        response_format="json_object",
        template=(
            "Analysiere den folgenden extrahierten Text eines "
            "{{ scope }}-Konzeptdokuments und identifiziere die Struktur:\n\n"
            "**Dokumenttitel:** {{ title|default('Unbekannt') }}\n"
            "**Fachbereich:** {{ scope }}\n"
            "**Seitenanzahl:** {{ page_count|default(0) }}\n\n"
            "**Extrahierter Text (gekürzt):**\n{{ text }}\n\n"
            "Erstelle eine Strukturanalyse im folgenden JSON-Format:\n"
            "{\n"
            '  "name": "Template-Name basierend auf dem Dokument",\n'
            '  "scope": "{{ scope }}",\n'
            '  "version": "1.0",\n'
            '  "is_master": false,\n'
            '  "framework": "Erkanntes Regelwerk (z.B. MBO, TRGS 720, VOB)",\n'
            '  "sections": [\n'
            "    {\n"
            '      "name": "abschnitt_id",\n'
            '      "title": "Kapiteltitel",\n'
            '      "description": "Kurzbeschreibung des Abschnitts",\n'
            '      "required": true,\n'
            '      "order": 1,\n'
            '      "fields": [\n'
            "        {\n"
            '          "name": "feld_id",\n'
            '          "label": "Feldbezeichnung",\n'
            '          "field_type": "text|textarea|number|date|choice|boolean",\n'
            '          "required": true,\n'
            '          "help_text": "Hinweis zum Feld",\n'
            '          "llm_hint": "Prompt-Hinweis für KI-Vorausfüllung",\n'
            '          "llm_prefill": true\n'
            "        }\n"
            "      ],\n"
            '      "subsections": []\n'
            "    }\n"
            "  ],\n"
            '  "confidence": 0.85,\n'
            '  "gaps": ["Fehlender Abschnitt X"],\n'
            '  "recommendations": ["Empfehlung 1"]\n'
            "}"
        ),
        variables=["scope", "title", "page_count", "text"],
    ),
    PromptTemplate(
        id="concept.task.merge_templates",
        layer=TemplateLayer.TASK,
        cacheable=False,
        phase="analysis",
        response_format="json_object",
        template=(
            "Du erhältst {{ template_count }} analysierte Konzept-Strukturen "
            "aus dem Fachbereich {{ scope }}.\n\n"
            "Erstelle daraus ein konsolidiertes Master-Template, das die "
            "häufigsten und wichtigsten Abschnitte und Felder enthält.\n\n"
            "**Analysierte Strukturen:**\n{{ templates_json }}\n\n"
            "Erstelle das Master-Template im folgenden JSON-Format:\n"
            "{\n"
            '  "name": "Master-Template {{ scope }}",\n'
            '  "scope": "{{ scope }}",\n'
            '  "version": "1.0",\n'
            '  "is_master": true,\n'
            '  "framework": "Hauptsächlich verwendetes Regelwerk",\n'
            '  "sections": [\n'
            "    {\n"
            '      "name": "abschnitt_id",\n'
            '      "title": "Kapiteltitel",\n'
            '      "description": "Beschreibung",\n'
            '      "required": true,\n'
            '      "order": 1,\n'
            '      "fields": [\n'
            "        {\n"
            '          "name": "feld_id",\n'
            '          "label": "Feldbezeichnung",\n'
            '          "field_type": "text|textarea|number|date|choice|boolean",\n'
            '          "required": true,\n'
            '          "help_text": "Hinweis"\n'
            "        }\n"
            "      ],\n"
            '      "subsections": []\n'
            "    }\n"
            "  ],\n"
            '  "confidence": 0.9,\n'
            '  "gaps": [],\n'
            '  "recommendations": ["Empfehlung"]\n'
            "}"
        ),
        variables=["template_count", "scope", "templates_json"],
    ),
    PromptTemplate(
        id="concept.task.prefill_field",
        layer=TemplateLayer.TASK,
        cacheable=False,
        phase="prefill",
        template=(
            "Schlage einen passenden Wert für das folgende Formularfeld vor:\n\n"
            "**Feld:** {{ field_key }}\n"
            "**Hinweis:** {{ llm_hint }}\n"
            "{% if context_values %}"
            "**Bereits ausgefüllte Werte:**\n{{ context_values }}\n"
            "{% endif %}"
            "{% if extracted_text %}"
            "**Extrahierter Dokumenttext (Auszug):**\n{{ extracted_text }}\n"
            "{% endif %}\n"
            "Antworte NUR mit dem vorgeschlagenen Wert."
        ),
        variables=[
            "field_key",
            "llm_hint",
            "context_values",
            "extracted_text",
        ],
    ),
]


def get_concept_analysis_stack() -> PromptStack:
    """
    Return a PromptStack pre-seeded with all concept-analysis templates.

    Each call returns a new independent stack instance.

    Example::

        stack = get_concept_analysis_stack()

        # Document structure analysis
        rendered = stack.render_stack(
            ["concept.system.analyst", "concept.task.analyze_structure"],
            context={
                "scopes": "Brandschutz, Explosionsschutz",
                "language": "de",
                "scope": "explosionsschutz",
                "title": "Ex-Schutz Dokument",
                "page_count": 12,
                "text": "Extrahierter Text...",
            },
        )
        # rendered.system, rendered.user

        # Template merging
        messages = stack.render_to_messages(
            ["concept.system.merger", "concept.task.merge_templates"],
            context={
                "language": "de",
                "scope": "brandschutz",
                "template_count": 3,
                "templates_json": "[...]",
            },
        )

        # Field prefill
        rendered = stack.render_stack(
            ["concept.system.prefill", "concept.task.prefill_field"],
            context={
                "scope": "explosionsschutz",
                "language": "de",
                "field_key": "zoneneinteilung__zone_typ",
                "llm_hint": "Bestimme den Zonentyp",
                "extracted_text": "...",
            },
        )
    """
    stack = PromptStack()
    for tmpl in CONCEPT_ANALYSIS_TEMPLATES:
        stack.register(tmpl)
    return stack
