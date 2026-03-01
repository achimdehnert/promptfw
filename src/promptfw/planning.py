"""Built-in planning-phase prompt templates per format type.

Provides a pre-seeded PromptStack with planning templates for all
supported content formats. Templates follow the 4-layer pattern:
SYSTEM → FORMAT → CONTEXT → TASK.

Usage::

    from promptfw.planning import get_planning_stack

    stack = get_planning_stack()
    rendered = stack.render("academic.task.planning", {
        "title": "KI in der Medizin",
        "field_of_study": "Medizininformatik",
        "description": "Auswirkungen von LLMs auf Diagnosestellung",
        "citation_style": "APA",
    })
    # rendered.system  →  system prompt
    # rendered.user    →  user prompt with research question task
"""

from __future__ import annotations

from promptfw.schema import PromptTemplate, TemplateLayer
from promptfw.stack import PromptStack

PLANNING_TEMPLATES: list[PromptTemplate] = [
    # -------------------------------------------------------------------------
    # ROMAN / NOVEL
    # -------------------------------------------------------------------------
    PromptTemplate(
        id="roman.task.planning",
        layer=TemplateLayer.TASK,
        format_type="roman",
        phase="planning",
        task="planning",
        template=(
            "Entwickle die Planungsgrundlagen für ein {{ genre }}-Projekt mit dem Titel '{{ title }}'.\n"
            "Beschreibung: {{ description }}\n\n"
            "Erstelle:\n"
            "1. Prämisse (2-3 Sätze): Die zentrale Idee und das Herz der Geschichte.\n"
            "2. Drei zentrale Themen (als Liste).\n"
            "3. Logline (1 Satz): Protagonist + Ziel + Hindernis + Einsatz.\n\n"
            "Antworte als JSON: {\"premise\": \"...\", \"themes\": [\"...\"], \"logline\": \"...\"}"
        ),
        variables=["title", "genre", "description"],
    ),
    PromptTemplate(
        id="roman.system.planning",
        layer=TemplateLayer.SYSTEM,
        format_type="roman",
        phase="planning",
        cacheable=True,
        template=(
            "Du bist ein erfahrener Lektor und Story-Entwickler für literarische Werke. "
            "Du hilfst Autoren dabei, die Grundlagen ihrer Geschichte zu entwickeln. "
            "Deine Antworten sind präzise, kreativ und auf die Zielgruppe abgestimmt. "
            "Antworte immer auf Deutsch, sofern nicht anders angegeben."
        ),
        variables=[],
    ),
    # -------------------------------------------------------------------------
    # NONFICTION / SACHBUCH
    # -------------------------------------------------------------------------
    PromptTemplate(
        id="nonfiction.task.planning",
        layer=TemplateLayer.TASK,
        format_type="nonfiction",
        phase="planning",
        task="planning",
        template=(
            "Entwickle die Planungsgrundlagen für ein Sachbuch mit dem Titel '{{ title }}'.\n"
            "Thema/Beschreibung: {{ description }}\n"
            "{% if field_of_study %}Fachgebiet: {{ field_of_study }}\n{% endif %}"
            "\nErstelle:\n"
            "1. Kernbotschaft (2-3 Sätze): Was ist das zentrale Thema und welchen Nutzen hat das Buch?\n"
            "2. Drei Hauptthemen (als Liste).\n"
            "3. Kurzzusammenfassung (Abstract, 100 Wörter): Für wen ist das Buch und was lernen Leser?\n"
            "4. Primäre Zielgruppe (1 Satz).\n\n"
            "Antworte als JSON: {\"core_message\": \"...\", \"themes\": [\"...\"], "
            "\"abstract\": \"...\", \"target_audience\": \"...\"}"
        ),
        variables=["title", "description"],
    ),
    PromptTemplate(
        id="nonfiction.system.planning",
        layer=TemplateLayer.SYSTEM,
        format_type="nonfiction",
        phase="planning",
        cacheable=True,
        template=(
            "Du bist ein erfahrener Sachbuch-Lektor und Content-Stratege. "
            "Du hilfst Autoren dabei, die Kernbotschaft und Struktur ihres Sachbuchs zu entwickeln. "
            "Deine Antworten sind klar, leserfreundlich und zielorientiert. "
            "Antworte immer auf Deutsch, sofern nicht anders angegeben."
        ),
        variables=[],
    ),
    # -------------------------------------------------------------------------
    # ACADEMIC / WISSENSCHAFTLICHES BUCH
    # -------------------------------------------------------------------------
    PromptTemplate(
        id="academic.task.planning",
        layer=TemplateLayer.TASK,
        format_type="academic",
        phase="planning",
        task="planning",
        template=(
            "Entwickle die wissenschaftliche Planungsgrundlage für eine akademische Arbeit:\n"
            "Titel: '{{ title }}'\n"
            "Fachgebiet: {{ field_of_study }}\n"
            "Beschreibung: {{ description }}\n"
            "{% if citation_style %}Zitationsstil: {{ citation_style }}\n{% endif %}"
            "\nErstelle:\n"
            "1. Forschungsfrage (1-2 Sätze): Klar und präzise formuliert.\n"
            "2. Zielsetzung (2-3 Sätze): Was soll die Arbeit zeigen/beweisen/entwickeln?\n"
            "3. Abstract (ca. 150 Wörter): Fragestellung, Methode, erwartete Ergebnisse, Relevanz.\n"
            "4. Fünf wissenschaftliche Keywords.\n\n"
            "Antworte als JSON: {\"research_question\": \"...\", \"objective\": \"...\", "
            "\"abstract\": \"...\", \"keywords\": [\"...\"]}"
        ),
        variables=["title", "field_of_study", "description"],
    ),
    PromptTemplate(
        id="academic.system.planning",
        layer=TemplateLayer.SYSTEM,
        format_type="academic",
        phase="planning",
        cacheable=True,
        template=(
            "Du bist ein erfahrener wissenschaftlicher Betreuer und akademischer Schreibcoach. "
            "Du unterstützt Autoren beim Entwickeln von Forschungsfragen, Zielsetzungen und Abstracts "
            "für akademische Monographien, Dissertationen und Habilitationsschriften. "
            "Deine Antworten sind präzise, objektiv und folgen akademischen Standards. "
            "Antworte immer auf Deutsch, sofern nicht anders angegeben."
        ),
        variables=[],
    ),
    # -------------------------------------------------------------------------
    # SCIENTIFIC / WISSENSCHAFTLICHE ARBEIT (Paper, Studie)
    # -------------------------------------------------------------------------
    PromptTemplate(
        id="scientific.task.planning",
        layer=TemplateLayer.TASK,
        format_type="scientific",
        phase="planning",
        task="planning",
        template=(
            "Entwickle die wissenschaftliche Planungsgrundlage für eine Studie/Paper:\n"
            "Titel: '{{ title }}'\n"
            "Fachgebiet: {{ field_of_study }}\n"
            "Beschreibung: {{ description }}\n"
            "{% if citation_style %}Zitationsstil: {{ citation_style }}\n{% endif %}"
            "\nErstelle nach IMRaD-Struktur:\n"
            "1. Forschungsfrage (1 Satz).\n"
            "2. Haupthypothese (H1, 1-2 Sätze).\n"
            "3. Nullhypothese (H0, 1 Satz).\n"
            "4. Abstract (IMRaD, ca. 200 Wörter): Introduction / Methods / Results / Discussion.\n"
            "5. Fünf Keywords für die Literaturdatenbank.\n\n"
            "Antworte als JSON: {\"research_question\": \"...\", \"hypothesis\": \"...\", "
            "\"null_hypothesis\": \"...\", \"abstract\": \"...\", \"keywords\": [\"...\"]}"
        ),
        variables=["title", "field_of_study", "description"],
    ),
    PromptTemplate(
        id="scientific.system.planning",
        layer=TemplateLayer.SYSTEM,
        format_type="scientific",
        phase="planning",
        cacheable=True,
        template=(
            "Du bist ein erfahrener Forschungsbegleiter und wissenschaftlicher Schreibcoach "
            "mit Expertise in empirischer Forschungsmethodik. "
            "Du hilfst Forschern beim Formulieren von Hypothesen, Forschungsfragen und IMRaD-Abstracts. "
            "Deine Antworten sind streng objektiv, methodisch präzise und folgen akademischen Standards. "
            "Antworte immer auf Deutsch, sofern nicht anders angegeben."
        ),
        variables=[],
    ),
    # -------------------------------------------------------------------------
    # ESSAY
    # -------------------------------------------------------------------------
    PromptTemplate(
        id="essay.task.planning",
        layer=TemplateLayer.TASK,
        format_type="essay",
        phase="planning",
        task="planning",
        template=(
            "Entwickle die argumentative Grundlage für einen Essay:\n"
            "Titel: '{{ title }}'\n"
            "Thema/Beschreibung: {{ description }}\n\n"
            "Erstelle:\n"
            "1. Hauptthese (1-2 Sätze): Die zentrale Position des Essays.\n"
            "2. Drei Hauptargumente (als Liste), die die These stützen.\n"
            "3. Gegenargument (1 Satz): Stärkster Einwand gegen die These.\n"
            "4. Schlussrichtung (1 Satz): Wie wird der Essay enden/auflösen?\n\n"
            "Antworte als JSON: {\"thesis\": \"...\", \"main_arguments\": [\"...\"], "
            "\"counter_argument\": \"...\", \"conclusion_direction\": \"...\"}"
        ),
        variables=["title", "description"],
    ),
    PromptTemplate(
        id="essay.system.planning",
        layer=TemplateLayer.SYSTEM,
        format_type="essay",
        phase="planning",
        cacheable=True,
        template=(
            "Du bist ein erfahrener Essayist und Rhetoriker. "
            "Du unterstützt Autoren beim Entwickeln von klaren Thesen und überzeugenden Argumentationsstrukturen. "
            "Deine Antworten sind klar, intellektuell präzise und argumentativ stark. "
            "Antworte immer auf Deutsch, sofern nicht anders angegeben."
        ),
        variables=[],
    ),
]


def get_planning_stack() -> PromptStack:
    """Return a PromptStack pre-seeded with all planning-phase templates.

    Usage::

        stack = get_planning_stack()
        rendered = stack.render("academic.task.planning", {
            "title": "KI in der Medizin",
            "field_of_study": "Medizininformatik",
            "description": "...",
            "citation_style": "APA",
        })
    """
    stack = PromptStack()
    for tmpl in PLANNING_TEMPLATES:
        stack.register(tmpl)
    return stack
