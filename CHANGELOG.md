# Changelog — promptfw

## [Unreleased]

## [0.5.0] — 2026-03-01

### Added
- `django_registry.py` — `DjangoTemplateRegistry` optional Django adapter for loading promptfw templates from Django ORM querysets (`pip install promptfw[django]`)
  - `from_queryset(queryset, field_map, strict)` — converts ORM objects to `PromptTemplate` instances
  - Automatic SYSTEM/TASK split: `system_prompt` → cacheable SYSTEM template, `user_prompt_template` → TASK template
  - `BFAGENT_FIELD_MAP` — ready-to-use field map for the bfagent `PromptTemplate` model
  - `strict=True` raises `ValueError` on first conversion error (production); `strict=False` logs warning and skips (development)
  - Custom `field_map` support — works with any ORM model layout via string attribute names or callables
- `DjangoTemplateRegistry` and `BFAGENT_FIELD_MAP` exported from top-level `promptfw` package
- `promptfw[django]` optional dependency group (`django>=4.2`)

### Fixed (ADR review — 11 Befunde)
- `LLMResponseError` — new exception class for LLM response parsing failures (distinct from `TemplateRenderError` for Jinja2 rendering failures); `extract_json_strict()` now raises `LLMResponseError` instead of `TemplateRenderError`
- `renderer.py` — `output_schema`/`response_format` propagation now restricted to **TASK-layer templates only** (was: all layers — bug)
- `registry.py` — `from_directory(strict=False)` new parameter: `strict=True` raises `ValueError` on malformed YAML instead of silent log+skip; `response_format` validated against `VALID_RESPONSE_FORMATS` at load time
- `schema.py` — `VALID_RESPONSE_FORMATS` constant (`{"json_object", "json_schema", "text"}`); `Literal` annotation on `response_format` in `PromptTemplate` and `RenderedPrompt`
- `LLMResponseError`, `VALID_RESPONSE_FORMATS` exported from top-level package

### Changed
- ADR-001: title 4-Layer → 5-Layer; two ID namespaces documented; invariants + thread-safety warning
- ADR-002: strict-mode documented; hot-reload Docker limitation; response_format validation
- ADR-003: `output_format` → `response_format`; `LLMResponseError` hierarchy; TASK-only invariant; PromptStackService migration gate
- `pyproject.toml` description: "4-layer" → "5-layer"

## [0.4.0] — 2026-03-01

### Added
- `parsing.py` — `extract_json()`, `extract_json_list()`, `extract_json_strict()` for reliable JSON extraction from LLM responses (handles markdown-fenced, plain-fenced, raw JSON)
- `extract_json`, `extract_json_list`, `extract_json_strict` exported from top-level `promptfw` package
- `writing.py` — built-in writing-phase templates for long-form content production:
  - `writing.system.author`, `writing.system.editor` (cacheable)
  - `writing.format.roman`, `writing.format.nonfiction`, `writing.format.series` (cacheable)
  - `writing.task.write_chapter`, `write_scene`, `generate_outline`, `improve_prose`, `add_dialogue`, `summarize`
- `get_writing_stack()` — pre-seeded `PromptStack` for all writing-phase templates
- `get_writing_stack` and `WRITING_TEMPLATES` exported from top-level `promptfw` package
- `lektorat.py` — built-in lektorat (manuscript analysis) templates:
  - `lektorat.system.analyst` (cacheable)
  - `lektorat.task.extract_characters`, `check_consistency`, `analyze_style`, `find_repetitions`, `check_timeline` (all with `response_format="json_object"`)
- `get_lektorat_stack()` — pre-seeded `PromptStack` for all lektorat templates
- `get_lektorat_stack` and `LEKTORAT_TEMPLATES` exported from top-level `promptfw` package
- `PromptTemplate.output_schema` — JSON Schema dict for OpenAI/LiteLLM `response_format=json_schema`
- `PromptTemplate.response_format` — `"json_object"` / `"json_schema"` / `"text"` hint
- `RenderedPrompt.output_schema` and `RenderedPrompt.response_format` — propagated from last TASK template in `render_stack()`
- ADR documentation: `docs/adr/ADR-001` (four-layer stack), `ADR-002` (YAML vs DB registry), `ADR-003` (extension roadmap)

### Fixed
- `PromptRenderer.render_template()` now pre-fills variables declared in `template.variables` but absent from `context` with `None`, enabling `{% if var %}` guards without requiring callers to pass every optional variable

## [0.3.0] — 2026-03-01

### Added
- `planning.py` — built-in planning-phase templates for `roman`, `nonfiction`, `academic`, `scientific`, `essay`
- `get_planning_stack()` — pre-seeded `PromptStack` for all planning formats
- `get_planning_stack` and `PLANNING_TEMPLATES` exported from top-level `promptfw` package

### Fixed
- `pydantic` removed from required `dependencies` (was declared but never used — ghost dependency)
- `pyyaml` moved from `optional-dependencies[all]` to required `dependencies` (needed for `from_directory()`)
- `few_shot_messages` is now a proper `RenderedPrompt` dataclass field instead of a dynamic `setattr`
- Wildcard sort in `TemplateRegistry.get()` now resolves by ID length (most specific wins) instead of a no-op `*`-count on template IDs
- Corrected `project.urls` in `pyproject.toml` to point to `achimdehnert/promptfw`

## [0.2.0] — 2026-02-28

### Added
- `TemplateRegistry`: version-pinning via `template_id@version` syntax
- `TemplateRegistry`: hot-reload via `watchdog` (`registry.enable_hot_reload()`)
- `TemplateRegistry.from_directory()`: strict required-field validation on YAML load
- `PromptRenderer.render_to_messages()` — renders stack directly to OpenAI/LiteLLM messages list
- Few-shot examples rendered as interleaved `user`/`assistant` messages

## [0.1.0] — 2026-02-28

### Added
- Initial release
- `PromptTemplate` dataclass with 4 layers (SYSTEM, FORMAT, CONTEXT, TASK, FEW_SHOT)
- `TemplateRegistry` with exact and wildcard (`fnmatch`) lookup
- `PromptRenderer` — Jinja2 `StrictUndefined`, system/user split, token estimation
- `PromptStack` façade — `render()`, `render_stack()`, `from_directory()`
- `TemplateNotFoundError`, `TemplateRenderError` with informative messages
- Optional tiktoken integration for accurate token counting
- YAML template loading via `PromptStack.from_directory()`
