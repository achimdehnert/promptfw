# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-03-01

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
