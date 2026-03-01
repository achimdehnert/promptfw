# ADR-003: Erweiterungsroadmap — writing, lektorat, parsing, output_schema

| Metadata | Value |
|----------|-------|
| **Status** | Proposed |
| **Date** | 2026-03-01 |
| **Author** | Achim Dehnert |
| **Reviewers** | — |
| **Supersedes** | — |
| **Related** | ADR-001 (Four-Layer Stack), ADR-002 (YAML vs. DB), bfagent ADR-080 |

---

## 1. Context

Die Analyse der bfagent-Codebase (Stand 2026-03-01) hat ergeben, dass promptfw in seiner aktuellen Form (v0.3.0) nur in `apps/writing_hub/services/prompt_stack_service.py` direkt genutzt wird. Der Rest von bfagent verwendet vier parallele, unverbundene Prompt-Systeme mit folgenden Mustern:

1. **Hardcodierte f-Strings / Inline-Prompts** — in `chapter_actions.py`, `style_lab_service.py`, `lektorat_service.py`, `outline_recommender_service.py`, `creative_agent_service.py` u.a. (>50 Stellen)
2. **`PromptFactory`** — DB-Templates + Jinja2-Cache (`apps/bfagent/services/prompt_factory.py`)
3. **`PromptFramework`** — SecureEngine + Circuit Breaker (`apps/core/services/prompt_framework/`)
4. **`PromptStackService`** — bereits promptfw-basiert (`apps/writing_hub/`)

Die größten Effizienzgewinne entstehen durch:
- Eliminierung duplizierter JSON-Parsing-Logik (~8 Stellen)
- Konsolidierung von Kapitel-Schreib-Prompts in ein `writing.py`-Modul
- Konsolidierung von Lektorats-Prompts in ein `lektorat.py`-Modul
- Einführung von `output_schema` + `response_format` für Structured Outputs

## 2. Decision

**promptfw wird in drei Phasen erweitert:**

---

### Phase 1 — Sofort (v0.4.0): `parsing.py` und `output_schema`

#### 1a. `promptfw/parsing.py` — JSON-Parsing-Utilities

**Problem:** JSON-Extraktion aus LLM-Antworten ist in bfagent 8× dupliziert:

```python
# Typisches Pattern in bfagent (8× wiederholt):
json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
if not json_match:
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
data = json.loads(json_match.group()) if json_match else {}
```

**Lösung:**
```python
# promptfw/parsing.py
def extract_json(text: str) -> dict | None:
    """Extract first JSON object from LLM response text."""

def extract_json_list(text: str) -> list:
    """Extract first JSON array from LLM response text."""

def extract_json_strict(text: str) -> dict:
    """Extract JSON or raise LLMResponseError."""
```

**Exception-Hierarchie (Befund #9 — Separation of Concern):**

`extract_json_strict()` wirft `LLMResponseError`, **nicht** `TemplateRenderError`. Begründung:

| Exception | Bedeutung | Auslöser |
|---|---|---|
| `TemplateRenderError` | Jinja2-Rendering fehlgeschlagen | Fehlendes Jinja2-Variable, Syntax-Fehler im Template |
| `LLMResponseError` | LLM-Antwort nicht verwertbar | Kein JSON in Response, leere Response |

Callers die `except TemplateRenderError` für Rendering-Fehler abfangen, fangen damit **nicht** versehentlich LLM-Response-Fehler. Die Trennung ist Pflicht — beide sind `PromptfwError`-Subklassen.

#### 1b. `PromptTemplate.output_schema` + `response_format`

**Problem:** bfagent's `PromptTemplate`-Modell hat `output_schema: JSONField` und `output_format`-Felder für Structured Outputs. promptfw kennt dieses Konzept nicht.

**Lösung:**
```python
@dataclass
class PromptTemplate:
    ...
    output_schema: dict | None = None
    response_format: Literal["json_object", "json_schema", "text"] | None = None
```

`render_stack()` propagiert `output_schema` und `response_format` auf `RenderedPrompt`, sodass sie direkt an `litellm.completion(response_format=...)` übergeben werden können.

**Invariante (Befund #10):** `response_format` und `output_schema` werden **ausschließlich von TASK-Layer-Templates** propagiert. SYSTEM- und FORMAT-Templates können diese Felder definieren, sie werden aber beim Rendering ignoriert. Begründung: Der Response-Vertrag (`json_object`, `json_schema`) gehört zur Task-Definition, nicht zur Rolle oder zum Format.

```python
# renderer.py — Invariante explizit im Code:
if tmpl.layer == TemplateLayer.TASK:          # nur TASK
    if tmpl.output_schema is not None:
        output_schema = tmpl.output_schema
    if tmpl.response_format is not None:
        response_format = tmpl.response_format
```

Gültige Werte: `VALID_RESPONSE_FORMATS = {"json_object", "json_schema", "text"}` (aus `schema.py`).

---

### Phase 2 — Kurzfristig (v0.5.0): `writing.py`

**Problem:** Kapitel-Schreib-Prompts sind in bfagent über mindestens 10 Dateien verteilt (`chapter_actions.py`, `write_scene.yaml`, `writing_llm_handler.py`, `chapter_production_service.py`, `chapter_regenerate_handler_v2.py`, `story_chapter_generate_handler.py` u.a.) ohne gemeinsame Basis.

**Lösung:** Neues Modul `promptfw/writing.py` analog zu `planning.py`:

```python
# Template-ID-Konvention: writing.<layer>.<task>
WRITING_TEMPLATES = [
    # System (stable, cacheable)
    PromptTemplate(id="writing.system.author",    layer=SYSTEM, cacheable=True, ...),
    # Format (stable, cacheable)
    PromptTemplate(id="writing.format.roman",     layer=FORMAT, cacheable=True, ...),
    PromptTemplate(id="writing.format.nonfiction",layer=FORMAT, cacheable=True, ...),
    PromptTemplate(id="writing.format.series",    layer=FORMAT, cacheable=True, ...),
    # Task (dynamic)
    PromptTemplate(id="writing.task.write_chapter",  layer=TASK, ...),
    PromptTemplate(id="writing.task.write_scene",    layer=TASK, ...),
    PromptTemplate(id="writing.task.improve_prose",  layer=TASK, ...),
    PromptTemplate(id="writing.task.add_dialogue",   layer=TASK, ...),
    PromptTemplate(id="writing.task.summarize",      layer=TASK, ...),
    PromptTemplate(id="writing.task.generate_outline", layer=TASK, ...),
]

def get_writing_stack() -> PromptStack: ...
```

**Kontext-Variablen (aus bfagent-Analyse):**
- `chapter_number`, `chapter_title`, `chapter_outline`
- `target_words`, `pov_character`, `mood`, `genre`
- `prior_chapter_summary`, `story_premise`

---

### Phase 3 — Mittelfristig (v0.6.0): `lektorat.py`

**Problem:** `LektoratService` (1354 Zeilen) baut alle Prompts inline als f-Strings. Die 5 Lektorats-Module (Figuren, Zeitlinie, Stil, Wiederholungen, Konsistenz) haben identische System-Prompt-Struktur.

**Lösung:** Neues Modul `promptfw/lektorat.py`:

```python
LEKTORAT_TEMPLATES = [
    PromptTemplate(id="lektorat.system.analyst",        layer=SYSTEM, cacheable=True, ...),
    PromptTemplate(id="lektorat.task.extract_characters", layer=TASK, response_format="json_object", ...),
    PromptTemplate(id="lektorat.task.check_consistency",  layer=TASK, response_format="json_object", ...),
    PromptTemplate(id="lektorat.task.analyze_style",      layer=TASK, response_format="json_object", ...),
    PromptTemplate(id="lektorat.task.find_repetitions",   layer=TASK, response_format="json_object", ...),
]

def get_lektorat_stack() -> PromptStack: ...
```

---

### Weitere geplante Erweiterungen (Backlog, ohne feste Version)

| Feature | Priorität | Beschreibung |
|---|---|---|
| `DjangoTemplateRegistry` | Mittel | `from_queryset(qs)` lädt bfagent `PromptTemplate`-Objekte |
| `context_scope` Sub-Layer | Mittel | `project` / `chapter` / `scene` für gestaffelten Context |
| `image_prompt.py` | Niedrig | Bild-Prompt-Templates für `ScenePromptBuilder` in bfagent |
| `render_with_fallback()` | Niedrig | Graceful Degradation bei fehlenden Templates |
| A/B-Testing in Registry | Niedrig | `register_ab_group(templates, weights)` |
| `list_by_phase()` | Niedrig | `registry.list_by_phase("writing")` |

## 3. Implementation

### Versionierungsplan

| Version | Feature | Breaking Change |
|---|---|---|
| v0.4.0 | `parsing.py`, `output_schema` auf `PromptTemplate` + `RenderedPrompt` | Nein — additive |
| v0.5.0 | `writing.py`, `get_writing_stack()` | Nein — additive |
| v0.6.0 | `lektorat.py`, `get_lektorat_stack()` | Nein — additive |

### Test-Anforderungen (je Phase)

Analog zu `test_planning.py`:
- `test_all_formats_have_system_template()`
- `test_system_templates_are_cacheable()`
- `test_template_ids_follow_convention()`
- `test_render_<format>_<task>()` für alle kritischen Kombinationen
- `test_extract_json_from_markdown_fenced_block()`
- `test_extract_json_from_raw_object()`
- `test_extract_json_list_from_response()`

### Auswirkung auf bfagent

Nach Implementierung kann bfagent:
- `from promptfw import get_writing_stack` statt Inline-Prompts in `chapter_actions.py`
- `from promptfw.parsing import extract_json` statt 8× dupliziertem Regex
- `from promptfw import get_lektorat_stack` statt Inline-Prompts in `lektorat_service.py`

Migrations-Strategie für bfagent: **Strangler Fig** — neue Implementierungen nutzen promptfw, bestehende Inline-Prompts werden schrittweise migriert ohne Breaking Changes (bfagent ADR-080).

### Migrationsgate: PromptStackService-Fehlerverhalten (Befund #11)

Der `PromptStackService` (`apps/writing_hub/services/prompt_stack_service.py`) ist das Migrations-Gate zwischen bfagent-DB-Templates und promptfw. Folgende Regeln gelten **ohne Ausnahme**:

1. **Kein stiller Fallback auf DB-Templates** wenn ein promptfw-Template fehlt. Ein fehlgeschlagenes `stack.get(template_id)` wirft `TemplateNotFoundError` — dieser darf nicht intern gefangen und durch ein DB-Template ersetzt werden ohne explizite Konfiguration.

2. **Explizite Fehlerbehandlung:** Wenn `PromptStackService` sowohl promptfw als auch DB-Templates unterstützen soll (Übergangsphase), muss das **konfigurativ gesteuert** sein — z.B. `use_promptfw: bool`-Flag auf dem Service, nicht durch implizites Exception-Catching.

3. **Verantwortlichkeit:** `PromptStackService` ist verantwortlich für die Konsistenz zwischen DB-Templates und promptfw-Built-ins. Bei Widerspruch (gleiche `id` in beiden) gewinnt promptfw-Built-in — dokumentiert im `PromptStackService`-Docstring.

```python
# apps/writing_hub/services/prompt_stack_service.py — Pflicht-Verhalten:
def render_writing_task(self, task_id: str, context: dict) -> list[dict]:
    try:
        stack = get_writing_stack()
        return stack.render_to_messages([...], context=context)
    except TemplateNotFoundError:
        # Explizit: kein stiller Fallback — Exception propagieren oder
        # explizit auf DB-Template umschalten wenn use_db_fallback=True
        raise  # oder: return self._render_from_db(task_id, context)
```

## 4. Consequences

### 4.1 Positive
- Eliminierung von ~8 duplizierten JSON-Parsing-Implementierungen in bfagent
- Kapitel-Schreib-Prompts an einer Stelle versionierbar und testbar
- `output_schema` ermöglicht direkte Structured-Output-Integration mit OpenAI/LiteLLM
- Klare Migrations-Strategie für bfagent via Strangler Fig

### 4.2 Negative
- Wachsende Bibliothek — mehr Abhängigkeiten für Nutzer die nur YAML-Registry brauchen
- `writing.py` und `lektorat.py` sind deutsch-sprachig (bfagent-spezifisch) — internationale Nutzer müssen eigene Templates erstellen

### 4.3 Mitigation
- Templates als Override-fähige YAML-Dateien dokumentieren
- `get_writing_stack(locale="de")` / `get_writing_stack(locale="en")` für Mehrsprachigkeit prüfen

## 5. Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-03-01 | Achim Dehnert | Initial draft — basierend auf bfagent-Codebase-Analyse |
| 2026-03-01 | Achim Dehnert | Review-Korrekturen: `output_format`→`response_format`; LLMResponseError-Hierarchie dokumentiert; TASK-only Invariante für response_format/output_schema; Migrationsgate PromptStackService mit Fehlerverhalten |
