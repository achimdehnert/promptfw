# ADR-001: Four-Layer Prompt Stack Architecture

| Metadata | Value |
|----------|-------|
| **Status** | Accepted |
| **Date** | 2026-03-01 |
| **Author** | Achim Dehnert |
| **Reviewers** | — |
| **Supersedes** | — |
| **Related** | bfagent ADR-079 (AI Authoring System) |

---

## 1. Context

promptfw is a standalone Python library for building structured LLM prompts used by bfagent (and potentially other platform applications). The core problem it solves: LLM prompts for long-form writing applications combine stable role definitions, format-specific rules, dynamic runtime context, and concrete task instructions — all in a single flat string. This makes prompts hard to maintain, version, and reuse across different writing phases.

The library needs a prompt composition model that:
- Separates stable (cacheable) parts from dynamic (per-request) parts
- Supports multi-format content (roman, nonfiction, academic, scientific, essay)
- Is compatible with OpenAI/LiteLLM message format (`system` + `user`)
- Can be loaded from YAML files for declarative management
- Works without a database dependency (standalone library, not Django-bound)

## 2. Decision

**Use a 5-layer named stack rendered into a 2-part output (system + user).**

### Layer definitions

| Layer | Output | Cacheable | Purpose |
|-------|--------|-----------|---------|
| `SYSTEM` | system prompt | ✅ | Role definition, base behaviour |
| `FORMAT` | system prompt | ✅ | Format-specific writing rules (roman, academic, …) |
| `CONTEXT` | user prompt | ❌ | Runtime context (characters, world, prior text) |
| `TASK` | user prompt | ❌ | Concrete task (what to write now) |
| `FEW_SHOT` | user prompt (interleaved) | ❌ | Example input/output pairs for in-context learning |

`SYSTEM` and `FORMAT` render into `RenderedPrompt.system` (stable, suitable for prompt caching).  
`CONTEXT`, `TASK`, and `FEW_SHOT` render into `RenderedPrompt.user` (dynamic per request).

### Why `dataclass` instead of Pydantic `BaseModel`

`PromptTemplate` and `RenderedPrompt` are value objects used purely within the library — no HTTP serialisation, no ORM, no JSON schema validation at the boundary. `dataclass` from stdlib has zero dependencies, is faster to instantiate, and is sufficient for structural typing. Pydantic would add ~10 MB of transitive dependencies with no benefit in this use case.

### Why YAML files instead of DB-backed registry

promptfw is a **standalone library**, not a Django app. It must work without a database, Django ORM, or any web framework. YAML files are version-control-friendly, human-readable, and sufficient for the declarative template management use case. Applications that require DB-backed templates (e.g., bfagent's `PromptFactory`) are responsible for their own adapter layer (see bfagent ADR-079).

### Why `fnmatch` wildcards instead of regex

The primary use case is hierarchical ID matching: `roman.*.scene_generation`. `fnmatch` is stdlib, has predictable glob semantics, and is sufficient for the dot-separated ID namespace. Regex would be more powerful but introduces friction for template authors.

## 3. Implementation

- `schema.py` — `TemplateLayer` (Enum), `PromptTemplate` (dataclass), `RenderedPrompt` (dataclass)
- `registry.py` — `TemplateRegistry`: exact lookup, wildcard (`fnmatch`), version-pinning (`id@version`), YAML `from_directory()`
- `renderer.py` — `PromptRenderer`: Jinja2 `StrictUndefined`, system/user split, few-shot interleaving, token estimation
- `stack.py` — `PromptStack`: façade combining registry + renderer; `render()`, `render_stack()`, `render_to_messages()`
- `planning.py` — pre-seeded planning-phase templates for all supported format types

### Template ID convention

```
<format_type>.<layer>.<task_name>
# Examples:
roman.system.planning
academic.task.planning
writing.format.roman
```

### Relationship to bfagent

bfagent uses promptfw via `apps/writing_hub/services/prompt_stack_service.py` (`PromptStackService`), which wraps `PromptStack.from_directory()` with a Jinja2 fallback. bfagent's `apps/core/services/prompt_framework/` is a separate, Django-bound system with circuit breakers and DB-backed templates — it is **not** a replacement for promptfw, but a higher-level resilience layer on top of it.

## 4. Consequences

### 4.1 Positive
- Zero mandatory dependencies beyond Jinja2 and PyYAML — installs in any Python environment
- Stable layers (`SYSTEM`, `FORMAT`) are naturally cacheable (Anthropic prompt caching, OpenAI prefix caching)
- `render_to_messages()` produces OpenAI/LiteLLM-compatible message lists directly
- YAML templates are version-controllable and diff-friendly
- No Django, no database — usable in scripts, notebooks, and non-Django services

### 4.2 Negative
- No built-in DB-backed template storage — applications needing DB templates must build their own adapter
- No async rendering support — Jinja2 rendering is synchronous (acceptable: rendering is CPU-bound and fast)
- YAML loading requires `pyyaml` — this is a required dependency, not optional

### 4.3 Mitigation
- DB adapter pattern is documented: `DjangoTemplateRegistry.from_queryset()` is a planned extension (see bfagent improvement backlog)
- `PromptStack` is designed to be subclassable for application-specific adapters

## 5. Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-03-01 | Achim Dehnert | Initial draft — retroactive documentation of v0.1.0–v0.3.0 decisions |
