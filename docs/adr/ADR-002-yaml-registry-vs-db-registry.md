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
| Hot-Reload | Ja (watchdog) | Polling oder Signals nötig |
| Notebook/Script-Nutzung | Ja | Nein |

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

## 4. Consequences

### 4.1 Positive
- promptfw ist ohne Django, ohne DB, ohne Dateisystem-Zugriff nutzbar (In-Code Built-ins)
- YAML-Templates sind Git-versionierbar und diff-bar
- Klare Schichttrennung: Library (promptfw) vs. Applikation (bfagent)
- Kein ORM-Overhead für einfache Template-Lookups

### 4.2 Negative
- Kein eingebautes A/B-Testing, Usage-Tracking, Fallback-Ketten
- DB-Adapter muss von der Applikation selbst implementiert werden
- YAML-Dateien müssen deployed werden (kein Admin-UI)

### 4.3 Mitigation
- `DjangoTemplateRegistry` als optionales `promptfw[django]`-Extra geplant (ADR-003)
- bfagent nutzt `PromptStackService` als Bridge zwischen DB-Templates und promptfw
- `TemplateRegistry` ist subklassierbar — eigene Adapter sind möglich

## 5. Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-03-01 | Achim Dehnert | Initial — retroaktive Dokumentation der v0.1.0–v0.3.0 Entscheidung |
