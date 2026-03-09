# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.5] — 2026-03-09

### Fixed
- `extract_field()`: continuation text now sliced from `m.end()` (end of header
  match) instead of `m.start()`, preventing the header line itself from leaking
  into the continuation when `pos` points at a leading `\n`. Introduced
  `_header_start()` helper for clean next-header boundary calculation.

## [0.5.4] — 2026-03-09

### Fixed
- `_FIELD_HEADER` regex: alternation pattern correctly handles `**Name:**`
  (colon inside bold markers) vs plain `Name:` / `### Name:` patterns.
- `extract_field()`: group indexing updated to match new alternation —
  `group(1)` = bold-colon name, `group(2)` = plain name, `group(3)` = value.

## [0.5.3] — 2026-03-09

### Fixed
- `_FIELD_HEADER` regex: added explicit alternation branch for `**Name:**`
  pattern where the colon appears before the closing `**`. Previous regex
  failed to extract the field name correctly for this common LLM output style.

## [0.5.2] — 2026-03-09

### Changed
- Internal release — version bump only; see 0.5.3 for the actual fix.

## [0.5.1] — 2026-03-09

### Changed
- Internal release — version bump only.

## [0.5.0] — 2026-03-01

### Added

- **`extract_field(text, field, default=None)`** in `promptfw.parsing` (#8)
  - Extracts named fields from Markdown-structured LLM responses
  - Handles `**Field:**`, `Field:`, `### Field` patterns (case-insensitive)
  - Value runs until next field header or end of string

- **`TemplateRegistry.get_or_fallback(patterns)`** (#7)
  - Tries each pattern in order, returns first match
  - Raises `TemplateNotFoundError` only if none match
  - Supports wildcards and version-pinned patterns

- **`PromptTemplate.tokens_estimate` auto-calculation** (#9)
  - Auto-calculated via `tiktoken` (`cl100k_base`) in `__post_init__` when `tokens_estimate=0`
  - Graceful fallback to `0` if `tiktoken` not installed (no breaking change)
  - Explicit non-zero values are never overridden

- **`PromptStack.render_with_fallback(patterns, context)`** (#3)
  - Renders first matching template from an ordered fallback list
  - Delegates to `registry.get_or_fallback()` then `renderer.render_stack()`
  - Raises `TemplateNotFoundError` if no pattern matches

- **Context scope sub-layers** (#2)
  - `TemplateLayer.CONTEXT_PROJECT`, `CONTEXT_CHAPTER`, `CONTEXT_SCENE`
  - `USER_LAYERS` tuple defines canonical render order:
    `CONTEXT → CONTEXT_PROJECT → CONTEXT_CHAPTER → CONTEXT_SCENE → TASK`
  - `PromptRenderer.render_stack()` auto-sorts templates by canonical layer order
  - Backward-compatible: existing `CONTEXT` layer templates unchanged

- **`PromptStack.for_format(format_type)`** (#6)
  - Returns a new `PromptStack` with only format-matching templates
  - Templates with `format_type=None` are always included (format-agnostic)
  - Chainable with all render methods
  - Shares renderer instance with parent stack

- **`PromptStack.render_to_messages(patterns, context)`** (#5)
  - Renders directly into OpenAI/LiteLLM `[{"role": ..., "content": ...}]` format
  - Includes few-shot examples as interleaved `user`/`assistant` messages

- **`extract_field`** and **`USER_LAYERS`** exported from `promptfw` top-level

### Changed

- `PromptRenderer.render_stack()` now auto-sorts templates by canonical layer order
  (SYSTEM/FORMAT → CONTEXT* → TASK → FEW_SHOT). Callers no longer need to sort.
- Module docstring in `parsing.py` updated to document both JSON and Markdown parsing
- `renderer.py` docstring updated to reflect 5-layer stack

### Tests

- `tests/test_extract_field.py` — 10 tests for `extract_field()`
- `tests/test_issues.py` — 17 tests for #2, #3, #7, #9
- `tests/test_for_format.py` — 7 tests for `for_format()`

## [0.4.x] and earlier

See git log for previous changes.
