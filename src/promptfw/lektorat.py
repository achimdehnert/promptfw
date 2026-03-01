"""
Built-in lektorat (manuscript editing/analysis) prompt templates.

Covers character extraction, consistency checking, style analysis,
repetition detection, and timeline verification.

Mirrors the pattern established in planning.py and writing.py.

Usage::

    from promptfw import get_lektorat_stack
    from promptfw.parsing import extract_json_list, extract_json

    stack = get_lektorat_stack()

    # Extract characters from a chapter
    messages = stack.render_to_messages(
        ["lektorat.system.analyst", "lektorat.task.extract_characters"],
        context={"content": chapter_text[:4000]},
    )
    response = llm_client.generate(messages)
    characters = extract_json_list(response)

    # Analyze writing style
    messages = stack.render_to_messages(
        ["lektorat.system.analyst", "lektorat.task.analyze_style"],
        context={"text": sample_text},
    )
    response = llm_client.generate(messages)
    style = extract_json(response)
"""

from __future__ import annotations

from promptfw.schema import PromptTemplate, TemplateLayer
from promptfw.stack import PromptStack

LEKTORAT_TEMPLATES: list[PromptTemplate] = [
    # =========================================================================
    # SYSTEM — stable, cacheable
    # =========================================================================
    PromptTemplate(
        id="lektorat.system.analyst",
        layer=TemplateLayer.SYSTEM,
        cacheable=True,
        phase="lektorat",
        template=(
            "Du bist ein erfahrener Literatur-Analyst und Lektor mit Expertise in:\n"
            "- Figurenanalyse und Charakterkonsistenz\n"
            "- Stilanalyse und Sprachmustern\n"
            "- Narrative Struktur und Zeitlinien\n"
            "- Wiederholungen und Redundanzen\n"
            "- Kontinuitätsfehlern\n\n"
            "Analysiere präzise und objektiv. "
            "Antworte IMMER im angeforderten JSON-Format ohne zusätzlichen Text."
        ),
        variables=[],
    ),
    # =========================================================================
    # TASK — dynamic, JSON output
    # =========================================================================
    PromptTemplate(
        id="lektorat.task.extract_characters",
        layer=TemplateLayer.TASK,
        cacheable=False,
        phase="lektorat",
        response_format="json_object",
        template=(
            "Analysiere den folgenden Textabschnitt und extrahiere alle "
            "erwähnten Figuren/Charaktere.\n\n"
            "Für jede Figur, gib folgende Informationen zurück (wenn vorhanden):\n"
            "- name: Hauptname der Figur\n"
            "- varianten: Andere Namen/Spitznamen (Liste)\n"
            "- rolle: protagonist/antagonist/hauptfigur/nebenfigur/erwaehnt\n"
            "- alter: Alter oder Altersangabe\n"
            "- geschlecht: männlich/weiblich/divers/unbekannt\n"
            "- haarfarbe: wenn erwähnt\n"
            "- augenfarbe: wenn erwähnt\n"
            "- besondere_merkmale: auffällige Merkmale\n"
            "- beruf: wenn erwähnt\n"
            "- charakterzuege: Persönlichkeitsmerkmale (Liste)\n\n"
            "{% if chapter_number %}Kapitel: {{ chapter_number }}\n{% endif %}"
            "TEXT:\n{{ content }}\n\n"
            "Antworte NUR als JSON-Array: "
            "[{\"name\": \"...\", \"varianten\": [], \"rolle\": \"...\", ...}]"
        ),
        variables=["content", "chapter_number"],
    ),
    PromptTemplate(
        id="lektorat.task.check_consistency",
        layer=TemplateLayer.TASK,
        cacheable=False,
        phase="lektorat",
        response_format="json_object",
        template=(
            "Prüfe die folgenden Figuren-Referenzen auf Inkonsistenzen.\n\n"
            "Bekannte Figuren-Daten:\n{{ known_characters }}\n\n"
            "Neue Referenzen aus Kapitel {{ chapter_number }}:\n{{ new_references }}\n\n"
            "Suche nach:\n"
            "- Widersprüchlichen Attributen (Haarfarbe, Augen, Alter, etc.)\n"
            "- Namensvarianten die nicht dokumentiert sind\n"
            "- Verhaltensinkonsistenzen gegenüber etabliertem Charakter\n\n"
            "Antworte NUR als JSON:\n"
            "{\"inconsistencies\": [{\"figur\": \"...\", \"typ\": \"...\", "
            "\"kapitel_alt\": 0, \"kapitel_neu\": 0, "
            "\"wert_alt\": \"...\", \"wert_neu\": \"...\", "
            "\"schwere\": \"hoch/mittel/niedrig\"}]}"
        ),
        variables=["known_characters", "chapter_number", "new_references"],
    ),
    PromptTemplate(
        id="lektorat.task.analyze_style",
        layer=TemplateLayer.TASK,
        cacheable=False,
        phase="lektorat",
        response_format="json_object",
        template=(
            "Analysiere den Schreibstil des folgenden Textes und extrahiere "
            "die charakteristischen Merkmale des Autors.\n\n"
            "Konzentriere dich auf:\n"
            "- Satzstruktur und Rhythmus (kurz/lang, Variation)\n"
            "- Wortwahl und Vokabular (einfach/komplex, Fremdwörter)\n"
            "- Narrative Perspektive und Nähe\n"
            "- Dialogführung (direkt/indirekt, Häufigkeit)\n"
            "- Beschreibungstechniken (sensorisch, metaphorisch)\n"
            "- Emotionale Tiefe und Subtext\n"
            "- Typische Sprachmuster und Stilmittel\n\n"
            "TEXT:\n{{ text }}\n\n"
            "Antworte NUR als JSON:\n"
            "{\"satzstruktur\": \"...\", \"wortwahl\": \"...\", "
            "\"perspektive\": \"...\", \"dialog\": \"...\", "
            "\"beschreibung\": \"...\", \"emotionale_tiefe\": \"...\", "
            "\"typische_muster\": [], \"stilmittel\": [], "
            "\"gesamteindruck\": \"...\"}"
        ),
        variables=["text"],
    ),
    PromptTemplate(
        id="lektorat.task.find_repetitions",
        layer=TemplateLayer.TASK,
        cacheable=False,
        phase="lektorat",
        response_format="json_object",
        template=(
            "Analysiere den folgenden Text auf Wiederholungen und Redundanzen.\n\n"
            "Suche nach:\n"
            "- Wörtern die übermäßig oft wiederholt werden\n"
            "- Phrasen oder Ausdrücke die mehrfach vorkommen\n"
            "- Inhaltlichen Wiederholungen (gleiche Information mehrfach)\n"
            "- Ähnlichen Satzanfängen in kurzer Folge\n\n"
            "{% if threshold %}Melde nur Wiederholungen ab {{ threshold }}× Vorkommen.\n{% endif %}"
            "TEXT:\n{{ text }}\n\n"
            "Antworte NUR als JSON:\n"
            "{\"wort_wiederholungen\": [{\"wort\": \"...\", \"anzahl\": 0, "
            "\"positionen\": []}], "
            "\"phrasen_wiederholungen\": [{\"phrase\": \"...\", \"anzahl\": 0}], "
            "\"inhaltliche_wiederholungen\": [\"...\"]}"
        ),
        variables=["text", "threshold"],
    ),
    PromptTemplate(
        id="lektorat.task.check_timeline",
        layer=TemplateLayer.TASK,
        cacheable=False,
        phase="lektorat",
        response_format="json_object",
        template=(
            "Prüfe die zeitliche Abfolge der Ereignisse im folgenden Text "
            "auf Widersprüche und Unklarheiten.\n\n"
            "{% if known_events %}Bekannte Zeitlinie:\n{{ known_events }}\n\n{% endif %}"
            "TEXT:\n{{ text }}\n\n"
            "Suche nach:\n"
            "- Zeitlichen Widersprüchen (Ereignis B vor A obwohl B nach A passieren sollte)\n"
            "- Unklaren Zeitsprüngen ohne Markierung\n"
            "- Inkonsistenten Zeitangaben (Tageszeit, Datum, Jahreszeit)\n"
            "- Flashbacks die nicht klar markiert sind\n\n"
            "Antworte NUR als JSON:\n"
            "{\"ereignisse\": [{\"beschreibung\": \"...\", \"zeitpunkt\": \"...\"}], "
            "\"widersprueche\": [{\"ereignis_a\": \"...\", \"ereignis_b\": \"...\", "
            "\"problem\": \"...\"}], "
            "\"unklarheiten\": [\"...\"]}"
        ),
        variables=["text", "known_events"],
    ),
]


def get_lektorat_stack() -> PromptStack:
    """
    Return a PromptStack pre-seeded with all lektorat (manuscript analysis) templates.

    Each call returns a new independent stack instance.

    Example::

        from promptfw import get_lektorat_stack
        from promptfw.parsing import extract_json_list, extract_json

        stack = get_lektorat_stack()

        # Extract characters
        messages = stack.render_to_messages(
            ["lektorat.system.analyst", "lektorat.task.extract_characters"],
            context={"content": chapter_text[:4000], "chapter_number": 3},
        )
        characters = extract_json_list(llm_client.generate(messages))

        # Style analysis
        messages = stack.render_to_messages(
            ["lektorat.system.analyst", "lektorat.task.analyze_style"],
            context={"text": sample_text},
        )
        style = extract_json(llm_client.generate(messages))
    """
    stack = PromptStack()
    for tmpl in LEKTORAT_TEMPLATES:
        stack.register(tmpl)
    return stack
