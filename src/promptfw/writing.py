"""
Built-in writing-phase prompt templates for long-form content production.

Covers chapter writing, scene generation, prose improvement, and related tasks.
Mirrors the pattern established in planning.py.

Usage::

    from promptfw import get_writing_stack

    stack = get_writing_stack()
    messages = stack.render_to_messages(
        ["writing.system.author", "writing.format.roman", "writing.task.write_chapter"],
        context={
            "chapter_number": 3,
            "chapter_title": "Die Rückkehr",
            "chapter_outline": "Der Held kehrt in sein Dorf zurück und findet es verändert.",
            "target_words": 2500,
            "pov_character": "Elias",
            "mood": "melancholic",
            "genre": "Fantasy",
            "prior_chapter_summary": "Elias überlebte die Schlacht und flieht in den Wald.",
            "story_premise": "Ein junger Schmied entdeckt seine magischen Kräfte.",
        },
    )
"""

from __future__ import annotations

from promptfw.schema import PromptTemplate, TemplateLayer
from promptfw.stack import PromptStack

WRITING_TEMPLATES: list[PromptTemplate] = [
    # =========================================================================
    # SYSTEM — stable, cacheable
    # =========================================================================
    PromptTemplate(
        id="writing.system.author",
        layer=TemplateLayer.SYSTEM,
        cacheable=True,
        format_type="roman",
        phase="writing",
        template=(
            "Du bist ein erfahrener Belletristik-Autor mit umfangreicher Erfahrung im "
            "Schreiben von Romanen und langen Erzählwerken.\n"
            "Deine Stärken:\n"
            "- Lebendige, szenische Beschreibungen die den Leser in die Welt ziehen\n"
            "- Authentische Charakterstimmen und Dialoge\n"
            "- Emotionale Tiefe und psychologische Glaubwürdigkeit\n"
            "- Erzählrhythmus der Spannung aufbaut und hält\n"
            "- Konsistenz in Stil, Ton und Figurenverhalten\n\n"
            "Schreibe immer in der vereinbarten Perspektive (POV) und halte den "
            "vorgegebenen Ton und die Stimmung durch das gesamte Kapitel."
        ),
        variables=[],
    ),
    PromptTemplate(
        id="writing.system.editor",
        layer=TemplateLayer.SYSTEM,
        cacheable=True,
        format_type="roman",
        phase="writing",
        template=(
            "Du bist ein erfahrener Lektor mit einem Gespür für Sprache, Struktur und "
            "Lesbarkeit.\n"
            "Deine Aufgabe ist es, bestehenden Text zu verbessern ohne seine Stimme zu verlieren.\n"
            "Grundsätze:\n"
            "- Behalte die Autorenstimme — ersetze nicht, verfeinere\n"
            "- Show, don't tell — stärke szenische Momente\n"
            "- Kürze Redundanzen ohne Substanz zu verlieren\n"
            "- Verbessere Satzrhythmus und Lesefluss\n"
            "- Stärke emotionale Wirkung durch präzisere Wortwahl"
        ),
        variables=[],
    ),
    # =========================================================================
    # FORMAT — stable, cacheable
    # =========================================================================
    PromptTemplate(
        id="writing.format.roman",
        layer=TemplateLayer.FORMAT,
        cacheable=True,
        format_type="roman",
        phase="writing",
        template=(
            "Format-Vorgaben für Roman-Kapitel:\n"
            "- Keine Kapitelüberschriften im Text selbst\n"
            "- Absätze: 3–6 Sätze, keine Wand aus Text\n"
            "- Dialoge: neue Zeile pro Sprecher, Gedankenstriche oder Anführungszeichen\n"
            "- Zeitform: Präteritum (sofern nicht anders vereinbart)\n"
            "- Perspective: konsequente POV-Disziplin\n"
            "- Kein Cliffhanger-Cliché am Ende — natürlicher Übergang oder emotionaler Abschluss"
        ),
        variables=[],
    ),
    PromptTemplate(
        id="writing.format.nonfiction",
        layer=TemplateLayer.FORMAT,
        cacheable=True,
        format_type="nonfiction",
        phase="writing",
        template=(
            "Format-Vorgaben für Sachbuch-Kapitel:\n"
            "- Strukturierte Absätze mit klarer Themenführung\n"
            "- Kernaussage pro Absatz, keine Dopplungen\n"
            "- Konkrete Beispiele und Belege für abstrakte Aussagen\n"
            "- Aktive Sprache, direkte Ansprache des Lesers wo passend\n"
            "- Zwischenüberschriften (H3) alle 400–600 Wörter\n"
            "- Kein akademischer Jargon ohne Erklärung"
        ),
        variables=[],
    ),
    PromptTemplate(
        id="writing.format.series",
        layer=TemplateLayer.FORMAT,
        cacheable=True,
        format_type="series",
        phase="writing",
        template=(
            "Format-Vorgaben für Serien-Band-Kapitel:\n"
            "- Band-interne Kontinuität: Figurenentwicklung und Plotfäden aufgreifen\n"
            "- Serien-Kontinuität: etablierte Welt, Regeln und Charakterisierungen konsistent halten\n"
            "- Kein vollständiges Recap am Kapitelanfang — kurze Einbettung reicht\n"
            "- Ende: Spannung für den nächsten Band/das nächste Kapitel aufbauen\n"
            "- Übergeordnete Serienthemen subtil einweben"
        ),
        variables=[],
    ),
    # =========================================================================
    # TASK — dynamic
    # =========================================================================
    PromptTemplate(
        id="writing.task.write_chapter",
        layer=TemplateLayer.TASK,
        cacheable=False,
        format_type="roman",
        phase="writing",
        template=(
            "Schreibe Kapitel {{ chapter_number }}: \"{{ chapter_title }}\"\n\n"
            "{% if story_premise %}Prämisse: {{ story_premise }}\n{% endif %}"
            "{% if prior_chapter_summary %}Zusammenfassung des vorherigen Kapitels:\n{{ prior_chapter_summary }}\n\n{% endif %}"
            "Outline dieses Kapitels:\n{{ chapter_outline }}\n\n"
            "Anforderungen:\n"
            "- Zielwortanzahl: {{ target_words|default(2500) }} Wörter\n"
            "- POV-Charakter: {{ pov_character|default('unbekannt') }}\n"
            "- Stimmung/Ton: {{ mood|default('neutral') }}\n"
            "- Genre: {{ genre|default('unbekannt') }}\n"
            "{% if scene_notes %}- Zusätzliche Hinweise: {{ scene_notes }}\n{% endif %}"
            "\nSchreibe den vollständigen Kapiteltext. Beginne direkt mit der Handlung."
        ),
        variables=[
            "chapter_number",
            "chapter_title",
            "chapter_outline",
            "target_words",
            "pov_character",
            "mood",
            "genre",
            "prior_chapter_summary",
            "story_premise",
            "scene_notes",
        ],
    ),
    PromptTemplate(
        id="writing.task.write_scene",
        layer=TemplateLayer.TASK,
        cacheable=False,
        format_type="roman",
        phase="writing",
        template=(
            "Schreibe die folgende Szene:\n\n"
            "Szenen-Beschreibung: {{ scene_description }}\n"
            "{% if characters %}Beteiligte Charaktere: {{ characters }}\n{% endif %}"
            "{% if location %}Ort: {{ location }}\n{% endif %}"
            "{% if mood %}Stimmung: {{ mood }}\n{% endif %}"
            "Zielumfang: {{ target_words|default(800) }} Wörter\n\n"
            "{% if scene_notes %}Hinweise: {{ scene_notes }}\n\n{% endif %}"
            "Schreibe die Szene vollständig und lebhaft."
        ),
        variables=[
            "scene_description",
            "characters",
            "location",
            "mood",
            "target_words",
            "scene_notes",
        ],
    ),
    PromptTemplate(
        id="writing.task.generate_outline",
        layer=TemplateLayer.TASK,
        cacheable=False,
        format_type="roman",
        phase="writing",
        template=(
            "Erstelle eine detaillierte Kapitel-Outline für Kapitel {{ chapter_number }}.\n\n"
            "{% if story_premise %}Prämisse: {{ story_premise }}\n{% endif %}"
            "{% if prior_chapter_summary %}Vorheriges Kapitel (Zusammenfassung): {{ prior_chapter_summary }}\n{% endif %}"
            "{% if story_arc %}Story Arc (aktuell): {{ story_arc }}\n{% endif %}"
            "{% if featured_characters %}Hauptfiguren in diesem Kapitel: {{ featured_characters }}\n{% endif %}"
            "Stimmung/Ton: {{ mood|default('neutral') }}\n\n"
            "Erstelle eine strukturierte Outline mit:\n"
            "1. **Eröffnungsszene** — Wie das Kapitel beginnt\n"
            "2. **Schlüsselereignisse** — 3–5 zentrale Ereignisse in Reihenfolge\n"
            "3. **Charakterentwicklung** — Welche Figur wächst/verändert sich wie\n"
            "4. **Spannungsbogen** — Wie Konflikt und Spannung aufgebaut werden\n"
            "5. **Abschluss** — Wie das Kapitel endet und in das nächste übergeht"
        ),
        variables=[
            "chapter_number",
            "story_premise",
            "prior_chapter_summary",
            "story_arc",
            "featured_characters",
            "mood",
        ],
    ),
    PromptTemplate(
        id="writing.task.improve_prose",
        layer=TemplateLayer.TASK,
        cacheable=False,
        format_type="roman",
        phase="writing",
        template=(
            "Verbessere den folgenden Textabschnitt. Behalte die Autorenstimme bei — "
            "verfeinere, ersetze nicht.\n\n"
            "Fokus der Verbesserung: {{ improvement_focus|default('allgemein') }}\n"
            "{% if style_notes %}Stil-Vorgaben: {{ style_notes }}\n{% endif %}"
            "\nOriginaltext:\n---\n{{ original_text }}\n---\n\n"
            "Gib nur den verbesserten Text zurück, keine Erklärungen."
        ),
        variables=["original_text", "improvement_focus", "style_notes"],
    ),
    PromptTemplate(
        id="writing.task.add_dialogue",
        layer=TemplateLayer.TASK,
        cacheable=False,
        format_type="roman",
        phase="writing",
        template=(
            "Ergänze den folgenden Abschnitt um einen authentischen Dialog.\n\n"
            "Beteiligte Charaktere: {{ characters }}\n"
            "Zweck des Dialogs: {{ dialogue_purpose }}\n"
            "{% if emotional_subtext %}Emotionaler Subtext: {{ emotional_subtext }}\n{% endif %}"
            "{% if style_notes %}Stil-Vorgaben: {{ style_notes }}\n{% endif %}"
            "\nKontext:\n---\n{{ context_text }}\n---\n\n"
            "Schreibe den Dialog nahtlos in den Kontext integriert. "
            "Jeder Charakter soll eine unverwechselbare Stimme haben."
        ),
        variables=[
            "characters",
            "dialogue_purpose",
            "emotional_subtext",
            "style_notes",
            "context_text",
        ],
    ),
    PromptTemplate(
        id="writing.task.summarize",
        layer=TemplateLayer.TASK,
        cacheable=False,
        format_type="roman",
        phase="writing",
        template=(
            "Erstelle eine präzise Zusammenfassung des folgenden Kapitel-Textes.\n\n"
            "Anforderungen:\n"
            "- Länge: {{ summary_length|default('150-200') }} Wörter\n"
            "- Fokus: Handlung, Charakterentwicklung, wichtige Informationen\n"
            "- Ton: neutral, informierend (nicht wertend)\n"
            "- Spoiler: vollständig (wird für interne Kontinuitätszwecke genutzt)\n\n"
            "Kapiteltext:\n---\n{{ chapter_text }}\n---"
        ),
        variables=["chapter_text", "summary_length"],
    ),
]


def get_writing_stack() -> PromptStack:
    """
    Return a PromptStack pre-seeded with all writing-phase templates.

    Each call returns a new independent stack instance.

    Example::

        stack = get_writing_stack()

        # Render a full chapter-writing prompt
        messages = stack.render_to_messages(
            ["writing.system.author", "writing.format.roman", "writing.task.write_chapter"],
            context={
                "chapter_number": 1,
                "chapter_title": "Der Aufbruch",
                "chapter_outline": "Elias verlässt das Dorf.",
                "target_words": 2500,
                "pov_character": "Elias",
                "mood": "hopeful",
                "genre": "Fantasy",
            },
        )

        # Render a prose improvement prompt
        messages = stack.render_to_messages(
            ["writing.system.editor", "writing.task.improve_prose"],
            context={
                "original_text": "Er ging schnell. Es war dunkel.",
                "improvement_focus": "Show don't tell, Rhythmus",
            },
        )
    """
    stack = PromptStack()
    for tmpl in WRITING_TEMPLATES:
        stack.register(tmpl)
    return stack
