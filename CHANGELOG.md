# Changelog — promptfw

## [Unreleased]

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
