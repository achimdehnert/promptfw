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
    # =========================================================================
    # SYSTEM — Academic / Scientific
    # =========================================================================
    PromptTemplate(
        id="writing.system.academic",
        layer=TemplateLayer.SYSTEM,
        cacheable=True,
        format_type="academic",
        phase="writing",
        template=(
            "Du bist ein erfahrener akademischer Autor und wissenschaftlicher Schreibcoach "
            "mit Expertise in Monographien, Dissertationen und Habilitationsschriften.\n"
            "Deine Stärken:\n"
            "- Präzise, objektive Sprache ohne rhetorische Übertreibungen\n"
            "- Klare Argumentationsstruktur mit These, Beleg und Schlussfolgerung\n"
            "- Korrekte Einbettung von Zitaten und Quellennachweisen\n"
            "- Konsistente Fachterminologie über das gesamte Werk\n"
            "- Strukturierte Absatzführung: ein Gedanke, eine Kernaussage\n\n"
            "Schreibe immer im akademischen Register: sachlich, präzise, nachvollziehbar. "
            "Verzichte auf wertende Allgemeinplätze und journalistische Stilmittel."
        ),
        variables=[],
    ),
    PromptTemplate(
        id="writing.system.scientific",
        layer=TemplateLayer.SYSTEM,
        cacheable=True,
        format_type="scientific",
        phase="writing",
        template=(
            "Du bist ein erfahrener Wissenschaftler und Erstautor für empirische Studien "
            "und wissenschaftliche Paper (IMRaD-Format).\n"
            "Deine Stärken:\n"
            "- Strikte IMRaD-Struktur: Introduction, Methods, Results, Discussion\n"
            "- Hypothesengeleitetes Schreiben: H1/H0 konsequent verfolgen\n"
            "- Objektive Ergebnisdarstellung ohne vorweggenommene Interpretation\n"
            "- Methodische Präzision: Stichprobe, Verfahren, Limitationen klar benennen\n"
            "- Korrekte statistische Notation und Signifikanzangaben\n\n"
            "Schreibe ausschließlich im wissenschaftlichen Register. "
            "Trenne Ergebnisse (Results) strikt von Interpretation (Discussion)."
        ),
        variables=[],
    ),
    # =========================================================================
    # FORMAT — Academic / Scientific
    # =========================================================================
    PromptTemplate(
        id="writing.format.academic",
        layer=TemplateLayer.FORMAT,
        cacheable=True,
        format_type="academic",
        phase="writing",
        template=(
            "Format-Vorgaben für akademische Monographien / Dissertationen:\n"
            "- Absätze: 4–8 Sätze, strenge Themenführung (ein Gedanke pro Absatz)\n"
            "- Zitate: direkte Zitate in Anführungszeichen + Quellenangabe (Autor Jahr: Seite)\n"
            "- Indirekte Zitate: paraphrasiert + Quellenangabe ohne Seitenzahl\n"
            "- Fußnoten: nur für ergänzende Hinweise, nicht für Hauptargumente\n"
            "- Überschriften: nummeriert (1., 1.1, 1.1.1), sachlich-deskriptiv\n"
            "- Zeitform: Präsens für allgemeingültige Aussagen, Perfekt für Forschungsstand\n"
            "- Keine Ich-Form (außer Vorwort), stattdessen 'Die vorliegende Arbeit zeigt...'\n"
            "- Abkürzungen: beim ersten Vorkommen ausschreiben, dann Kürzel"
        ),
        variables=[],
    ),
    PromptTemplate(
        id="writing.format.scientific",
        layer=TemplateLayer.FORMAT,
        cacheable=True,
        format_type="scientific",
        phase="writing",
        template=(
            "Format-Vorgaben für wissenschaftliche Paper (IMRaD):\n"
            "- Introduction: Forschungsstand → Forschungslücke → Fragestellung → Hypothese\n"
            "- Methods: Stichprobe, Design, Instrumente, Auswertungsverfahren — reproduzierbar\n"
            "- Results: nur Befunde, keine Interpretation — Tabellen/Abbildungen referenzieren\n"
            "- Discussion: Hypothesenprüfung, Einordnung, Limitationen, Ausblick\n"
            "- Statistik: M (SD), t(df) = x.xx, p = .xxx, d = x.xx (APA-Notation)\n"
            "- Zitation: nach vereinbartem Stil (APA/AMA/Vancouver etc.)\n"
            "- Passiv oder unpersönliche Konstruktionen: 'Es wurde analysiert...'\n"
            "- Abstract: max. 250 Wörter, strukturiert nach IMRaD-Kurzform"
        ),
        variables=[],
    ),
    # =========================================================================
    # TASK — Academic Section Writing
    # =========================================================================
    PromptTemplate(
        id="writing.task.write_academic_section",
        layer=TemplateLayer.TASK,
        cacheable=False,
        format_type="academic",
        phase="writing",
        template=(
            "Schreibe den folgenden Abschnitt der akademischen Arbeit:\n\n"
            "Titel der Arbeit: {{ work_title }}\n"
            "Abschnittstitel: {{ section_title }}\n"
            "Abschnittsnummer: {{ section_number|default('') }}\n"
            "{% if field_of_study %}Fachgebiet: {{ field_of_study }}\n{% endif %}"
            "{% if research_question %}Forschungsfrage: {{ research_question }}\n{% endif %}"
            "{% if section_outline %}Gliederung dieses Abschnitts:\n{{ section_outline }}\n{% endif %}"
            "{% if prior_section_summary %}Vorheriger Abschnitt (Zusammenfassung):\n{{ prior_section_summary }}\n{% endif %}"
            "{% if key_sources %}Zentrale Quellen (als Kontext, nicht direkt zitieren):\n{{ key_sources }}\n{% endif %}"
            "{% if citation_style %}Zitationsstil: {{ citation_style }}\n{% endif %}"
            "\nAnforderungen:\n"
            "- Zielumfang: {{ target_words|default(600) }} Wörter\n"
            "- Ton: akademisch, sachlich, präzise\n"
            "{% if additional_instructions %}- {{ additional_instructions }}\n{% endif %}"
            "\nSchreibe den vollständigen Abschnittstext. Beginne direkt mit dem Inhalt."
        ),
        variables=[
            "work_title",
            "section_title",
            "section_number",
            "field_of_study",
            "research_question",
            "section_outline",
            "prior_section_summary",
            "key_sources",
            "citation_style",
            "target_words",
            "additional_instructions",
        ],
    ),
    PromptTemplate(
        id="writing.task.write_imrad_section",
        layer=TemplateLayer.TASK,
        cacheable=False,
        format_type="scientific",
        phase="writing",
        template=(
            "Schreibe den folgenden IMRaD-Abschnitt:\n\n"
            "Paper-Titel: {{ paper_title }}\n"
            "Abschnitt: {{ imrad_section }}\n"
            "{% if field_of_study %}Fachgebiet: {{ field_of_study }}\n{% endif %}"
            "{% if hypothesis %}Hypothese (H1): {{ hypothesis }}\n{% endif %}"
            "{% if null_hypothesis %}Nullhypothese (H0): {{ null_hypothesis }}\n{% endif %}"
            "{% if section_outline %}Inhaltliche Vorgaben:\n{{ section_outline }}\n{% endif %}"
            "{% if methods_summary %}Methoden-Zusammenfassung (für Kontext):\n{{ methods_summary }}\n{% endif %}"
            "{% if results_summary %}Ergebnisse (für Discussion-Kontext):\n{{ results_summary }}\n{% endif %}"
            "{% if key_sources %}Schlüsselquellen:\n{{ key_sources }}\n{% endif %}"
            "{% if citation_style %}Zitationsstil: {{ citation_style }}\n{% endif %}"
            "\nAnforderungen:\n"
            "- Zielumfang: {{ target_words|default(500) }} Wörter\n"
            "- Strikte IMRaD-Konventionen einhalten\n"
            "- Results und Discussion klar trennen\n"
            "{% if additional_instructions %}- {{ additional_instructions }}\n{% endif %}"
            "\nSchreibe den Abschnitt vollständig. Beginne direkt mit dem Inhalt."
        ),
        variables=[
            "paper_title",
            "imrad_section",
            "field_of_study",
            "hypothesis",
            "null_hypothesis",
            "section_outline",
            "methods_summary",
            "results_summary",
            "key_sources",
            "citation_style",
            "target_words",
            "additional_instructions",
        ],
    ),
    PromptTemplate(
        id="writing.task.write_abstract",
        layer=TemplateLayer.TASK,
        cacheable=False,
        format_type="scientific",
        phase="writing",
        template=(
            "Schreibe einen strukturierten Abstract für folgende wissenschaftliche Arbeit:\n\n"
            "Titel: {{ work_title }}\n"
            "Typ: {{ work_type|default('Paper') }}\n"
            "{% if field_of_study %}Fachgebiet: {{ field_of_study }}\n{% endif %}"
            "{% if research_question %}Forschungsfrage: {{ research_question }}\n{% endif %}"
            "{% if hypothesis %}Hypothese: {{ hypothesis }}\n{% endif %}"
            "{% if methods_summary %}Methoden: {{ methods_summary }}\n{% endif %}"
            "{% if key_results %}Kernergebnisse: {{ key_results }}\n{% endif %}"
            "{% if conclusion %}Schlussfolgerung: {{ conclusion }}\n{% endif %}"
            "\nVorgaben:\n"
            "- Maximallänge: {{ max_words|default(250) }} Wörter\n"
            "- Struktur: Hintergrund / Ziel / Methoden / Ergebnisse / Schlussfolgerung\n"
            "- Keine Zitate, keine Abkürzungen ohne Erklärung\n"
            "- Unpersönliche Sprache (kein 'Ich' / 'Wir')\n"
            "\nSchreibe den Abstract als fließenden Text."
        ),
        variables=[
            "work_title",
            "work_type",
            "field_of_study",
            "research_question",
            "hypothesis",
            "methods_summary",
            "key_results",
            "conclusion",
            "max_words",
        ],
    ),
    PromptTemplate(
        id="writing.task.improve_academic_prose",
        layer=TemplateLayer.TASK,
        cacheable=False,
        format_type="academic",
        phase="writing",
        template=(
            "Verbessere den folgenden akademischen Text. Behalte den Inhalt und die "
            "Argumentation — verfeinere Sprache, Präzision und wissenschaftlichen Stil.\n\n"
            "{% if field_of_study %}Fachgebiet: {{ field_of_study }}\n{% endif %}"
            "Fokus der Verbesserung: {{ improvement_focus|default('Klarheit, Präzision, akademischer Stil') }}\n"
            "{% if citation_style %}Zitationsstil: {{ citation_style }}\n{% endif %}"
            "\nOriginaltext:\n---\n{{ original_text }}\n---\n\n"
            "Verbessere:\n"
            "- Unpräzise oder umgangssprachliche Formulierungen → akademisches Register\n"
            "- Redundante Aussagen → prägnante Formulierung\n"
            "- Unklare Kausalverknüpfungen → explizite Argumentationsschritte\n"
            "- Passiv/Aktiv nach akademischer Konvention\n\n"
            "Gib nur den verbesserten Text zurück, keine Erklärungen."
        ),
        variables=["original_text", "improvement_focus", "field_of_study", "citation_style"],
    ),
]


def get_writing_stack() -> PromptStack:
    """Return a PromptStack pre-seeded with all writing-phase templates."""
    stack = PromptStack()
    for tmpl in WRITING_TEMPLATES:
        stack.register(tmpl)
    return stack


def get_academic_writing_stack() -> PromptStack:
    """
    Return a PromptStack with academic writing templates only.

    Includes: writing.system.academic, writing.format.academic,
    writing.task.write_academic_section, writing.task.improve_academic_prose.

    Example::

        stack = get_academic_writing_stack()
        messages = stack.render_to_messages(
            [
                "writing.system.academic",
                "writing.format.academic",
                "writing.task.write_academic_section",
            ],
            context={
                "work_title": "KI-gestützte Diagnostik in der Medizin",
                "section_title": "Theoretischer Hintergrund",
                "section_number": "2.1",
                "field_of_study": "Medizininformatik",
                "research_question": "Wie verändern LLMs die klinische Entscheidungsfindung?",
                "target_words": 800,
                "citation_style": "APA",
            },
        )
    """
    academic_ids = {
        "writing.system.academic",
        "writing.format.academic",
        "writing.task.write_academic_section",
        "writing.task.improve_academic_prose",
        "writing.task.write_abstract",
    }
    stack = PromptStack()
    for tmpl in WRITING_TEMPLATES:
        if tmpl.id in academic_ids:
            stack.register(tmpl)
    return stack


def get_scientific_writing_stack() -> PromptStack:
    """
    Return a PromptStack with scientific (IMRaD) writing templates only.

    Includes: writing.system.scientific, writing.format.scientific,
    writing.task.write_imrad_section, writing.task.write_abstract.

    Example::

        stack = get_scientific_writing_stack()
        messages = stack.render_to_messages(
            [
                "writing.system.scientific",
                "writing.format.scientific",
                "writing.task.write_imrad_section",
            ],
            context={
                "paper_title": "LLM-Accuracy in Clinical Decision Support",
                "imrad_section": "Methods",
                "field_of_study": "Medical Informatics",
                "hypothesis": "LLMs erzielen eine Genauigkeit > 85 % bei Diagnosestellung.",
                "section_outline": "Stichprobe n=120, GPT-4o vs. Basisarzt-Urteil, Kappa-Koeffizient",
                "target_words": 600,
                "citation_style": "APA",
            },
        )
    """
    scientific_ids = {
        "writing.system.scientific",
        "writing.format.scientific",
        "writing.task.write_imrad_section",
        "writing.task.write_abstract",
    }
    stack = PromptStack()
    for tmpl in WRITING_TEMPLATES:
        if tmpl.id in scientific_ids:
            stack.register(tmpl)
    return stack
