# Changelog — promptfw

## [Unreleased]

### Added (v0.4.0 — planned)
- `parsing.py` — `extract_json()`, `extract_json_list()`, `extract_json_strict()` for reliable JSON extraction from LLM responses
- `extract_json`, `extract_json_list`, `extract_json_strict` exported from top-level `promptfw` package
- `writing.py` — built-in writing-phase templates: `writing.system.author`, `writing.system.editor`, `writing.format.roman/nonfiction/series`, `writing.task.write_chapter/write_scene/generate_outline/improve_prose/add_dialogue/summarize`
- `get_writing_stack()` — pre-seeded `PromptStack` for all writing-phase templates
- `get_writing_stack` and `WRITING_TEMPLATES` exported from top-level `promptfw` package
- `PromptRenderer.render_template()` now pre-fills declared variables absent from context with `None`, so `{% if var %}` guards work without passing all optional variables
- `lektorat.py` — built-in lektorat (manuscript analysis) templates: `lektorat.system.analyst`, `lektorat.task.extract_characters/check_consistency/analyze_style/find_repetitions/check_timeline`
- `get_lektorat_stack()` — pre-seeded `PromptStack` for all lektorat templates
- `get_lektorat_stack` and `LEKTORAT_TEMPLATES` exported from top-level `promptfw` package
- `PromptTemplate.output_schema` and `PromptTemplate.response_format` fields — propagated to `RenderedPrompt` by `render_stack()` (last TASK template wins)
- `RenderedPrompt.output_schema` and `RenderedPrompt.response_format` fields for direct use with OpenAI/LiteLLM `response_format` parameter

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
