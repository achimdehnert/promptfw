# ADR-002: YAML File Registry als primärer Template-Storage

| Metadata | Value |
|----------|-------|
| **Status** | Accepted |
| **Date** | 2026-03-01 |
| **Author** | Achim Dehnert |
| **Reviewers** | — |
| **Supersedes** | — |
| **Related** | ADR-001 (Four-Layer Stack), bfagent ADR-079 (AI Authoring System), bfagent ADR-080 |

---

## 1. Context

promptfw ist eine standalone Python-Bibliothek ohne Django-Abhängigkeit. Templates müssen irgendwo gespeichert und geladen werden. Drei grundsätzliche Optionen stehen zur Auswahl:

1. **YAML-Dateien** im Dateisystem
2. **Datenbank** (z.B. Django ORM, SQLAlchemy)
3. **In-Code** (Python `dataclass`-Instanzen, wie in `planning.py`)

In bfagent existiert zusätzlich ein `PromptTemplate`-Django-Modell mit A/B-Testing, Versionierung, Fallback-Ketten und Usage-Tracking. Die Frage ist, wie promptfw sich zu diesem Modell verhält.

## 2. Decision

**YAML-Dateien als primärer Storage; In-Code für Built-ins; DB als optionaler Adapter.**

### Primär: YAML-Dateien via `TemplateRegistry.from_directory()`

```yaml
# templates/writing/task/write_scene.yaml
id: writing.task.write_scene
layer: task
template: |
  Schreibe Kapitel {{ chapter_number }}: "{{ chapter_title }}"
  ...
variables: [chapter_number, chapter_title, chapter_outline]
cacheable: false
```

### Sekundär: In-Code Built-ins (`planning.py`, `writing.py`, `lektorat.py`)

Für Phase-spezifische Templates die Teil der Bibliothek selbst sind (planning, writing, lektorat) werden Templates direkt als `PromptTemplate`-Instanzen in Python-Modulen definiert. Sie sind immer verfügbar ohne Dateisystem-Zugriff.

### Optional: DB-Adapter (geplant, nicht implementiert)

```python
# Geplant in promptfw/contrib/django.py (ADR-003)
class DjangoTemplateRegistry(TemplateRegistry):
    @classmethod
    def from_queryset(cls, queryset) -> "DjangoTemplateRegistry": ...
```

## 3. Begründung

### Warum YAML statt DB als Primary Storage

| Kriterium | YAML | DB |
|---|---|---|
| Django-Abhängigkeit | Keine | Ja (Django ORM) oder SQLAlchemy |
| Versionskontrolle | Git-native, diff-bar | Migrations oder Dump nötig |
| Testbarkeit | `tmp_path` in pytest | DB-Fixture, `@pytest.mark.django_db` |
| Offline-Nutzung | Ja | Nein (DB-Verbindung nötig) |
| Hot-Reload (Development) | Ja, via watchdog (Volume-Mount) | Polling oder Signals nötig |
| Hot-Reload (Production) | **Nein** — Templates sind im Docker-Image eingebacken | Ja (DB ist persistent) |
| Notebook/Script-Nutzung | Ja | Nein |

> **Hinweis Hot-Reload in Docker/Production:** In `docker-compose.prod.yml` (Hetzner) sind YAML-Template-Dateien Teil des Container-Images. Ein Filesystem-Watcher (`watchdog`) würde niemals triggern, da keine Dateien zur Laufzeit geändert werden. `enable_hot_reload()` ist ausschließlich für `docker-compose.dev.yml` mit Volume-Mount vorgesehen. Siehe ADR-001 Thread-Safety-Warnung.

### Warum nicht DB als Primary Storage

bfagent hat ein vollständiges `PromptTemplate`-Django-Modell mit:
- `inheritance_parent` (Vererbung)
- `fallback_template` (Fallback-Kette)
- `ab_test_group` / `ab_test_weight` (A/B-Testing)
- `usage_count` / `last_used_at` (Usage-Tracking)
- Multi-Language-Support

Diese Features gehören in die **Applikationsschicht** (bfagent), nicht in die **Library-Schicht** (promptfw). promptfw bleibt schlank und framework-unabhängig.

### Warum In-Code für Built-ins

`planning.py` zeigt das Muster: Built-in Templates werden direkt in Python definiert, sind zero-dependency, und sind immer via `from promptfw import get_planning_stack` verfügbar. Dieses Muster wird auf `writing.py` und `lektorat.py` ausgeweitet (ADR-003).

### YAML-Load-Fehlerverhalten: strict vs. non-strict

**Problem:** Ein fehlerhaftes YAML (Syntaxfehler, fehlendes `template`-Feld, ungültiger `layer`-Wert) darf in Production nicht lautlos übergangen werden. Das entspräche einem stillen Fallback — verboten laut Qualitätskriterien.

**Entscheidung:** `TemplateRegistry.from_directory(strict: bool = False)`:

| Mode | Verhalten | Einsatz |
|---|---|---|
| `strict=False` (Default) | Fehlerhafte Templates werden geloggt und übersprungen | Development / Hot-Reload — ein in Bearbeitung befindliches YAML darf den Prozess nicht crashen |
| `strict=True` | `ValueError` bei erstem Fehler — kein Startup ohne valide Templates | **Production** (`docker-compose.prod.yml`) — Fehler müssen beim Container-Start sichtbar sein |

```python
# Production (settings/production.py):
registry = TemplateRegistry.from_directory(TEMPLATES_DIR, strict=True)

# Development (settings/development.py):
registry = TemplateRegistry.from_directory(TEMPLATES_DIR, strict=False)
```

### response_format-Validierung

`PromptTemplate.response_format` akzeptiert nur Werte aus `VALID_RESPONSE_FORMATS = {"json_object", "json_schema", "text"}` — aligniert mit der OpenAI/LiteLLM API. Die Validierung erfolgt beim YAML-Load (in `_load_yaml_file()`) und via `Literal`-Typannotation für statische Analyse. Ein ungültiger Wert (`"json_objekt"`) wird wie ein Feld-Fehler behandelt: im strict-Mode Exception, sonst Warning + Skip.

## 4. Consequences

### 4.1 Positive
- promptfw ist ohne Django, ohne DB, ohne Dateisystem-Zugriff nutzbar (In-Code Built-ins)
- YAML-Templates sind Git-versionierbar und diff-bar
- Klare Schichttrennung: Library (promptfw) vs. Applikation (bfagent)
- Kein ORM-Overhead für einfache Template-Lookups
- `strict=True` erzwingt valide Templates beim Container-Start — kein stiller Startup-Fehler in Production
- `response_format`-Validierung beim YAML-Load verhindert Tippfehler die erst zur LLM-API-Laufzeit auftreten

### 4.2 Negative
- Kein eingebautes A/B-Testing, Usage-Tracking, Fallback-Ketten
- DB-Adapter muss von der Applikation selbst implementiert werden
- YAML-Dateien müssen deployed werden (kein Admin-UI)
- Hot-Reload funktioniert **nicht** in Docker-Production (statisches Image) — nur in Dev mit Volume-Mount

### 4.3 Mitigation
- `DjangoTemplateRegistry` als optionales `promptfw[django]`-Extra geplant (ADR-003)
- bfagent nutzt `PromptStackService` als Bridge zwischen DB-Templates und promptfw
- `TemplateRegistry` ist subklassierbar — eigene Adapter sind möglich
- Production-Setting nutzt `strict=True` — Fehler sind sofort beim `docker-compose up` sichtbar

## 5. Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-03-01 | Achim Dehnert | Initial — retroaktive Dokumentation der v0.1.0–v0.3.0 Entscheidung |
| 2026-03-01 | Achim Dehnert | Review-Korrekturen: strict-Mode für YAML-Load; Hot-Reload Docker-Einschränkung; response_format-Validierung dokumentiert |
