# Changelog — promptfw

## [Unreleased]

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
