# AGENT_HANDOVER — iil-promptfw

> Living handover for the next agent/session. Keep this current; `NEXT.md` is an
> auto-generated cache and is **not** the source of truth — this file is.

## Current state (2026-06-22, observed)

- Version: `pyproject.toml` = **0.8.1**; CHANGELOG top entry = 0.8.1.
- Tests: green — `make test` → **251 passed** (1 warning), order-stable.
- Lint: `ruff check src/ tests/` clean.
- Types: no `[tool.mypy]` config, not part of the gate.
- CI: `.github/workflows/` = `ci.yml`, `test.yml`, `publish.yml`,
  `receive-windsurf-rules.yml`. `publish.yml` fires on `v*` tag or
  `workflow_dispatch` (PyPI).
- Package: `src/promptfw/`, ships `py.typed`, `__all__` declared.

## Recently landed (this PR — agent-readiness, no behavior change)

- `src/promptfw/__init__.py`: `__version__` now resolved from installed package
  metadata (`importlib.metadata.version("iil-promptfw")`, fallback
  `0.0.0.dev0`) instead of a hardcoded literal; added a public submodule-map
  docstring. `__all__` was already present and is kept.
- `pyproject.toml`: ruff `target-version` `py311` → `py312` (was a config-lie
  against `requires-python >=3.12`); deduped the duplicate
  `Programming Language :: Python :: 3.12` classifier and added the `3` parent.
- Added `CLAUDE.md` (repo operating guide) and this `AGENT_HANDOVER.md`.
- (Makefile already existed with working `test`/`lint`/`install`/`clean`.)

## Known issues / TODO

- **PyPI publish drift (priority, pre-existing — not touched here):** `pyproject`
  is at `0.8.1` but **0.8.1 is not published** on PyPI. The `__init__.py` literal
  had separately lagged at `0.7.0`, so the source had a three-way mismatch
  (`__init__` 0.7.0 vs `pyproject` 0.8.1 vs published PyPI). This PR removes the
  `__init__` source of drift (metadata-resolved version) but **deliberately does
  not change the version number or run any publish** — the failed/absent publish
  is a separate gated decision. Verify published version with
  `pip index versions iil-promptfw` before deciding.
- No `[tool.mypy]` config; no coverage floor configured.

## Next priorities

1. Decide/execute the gated `0.8.1` PyPI publish (resolves the publish drift).
2. Introduce a `[tool.mypy]` config (start lenient) and a `types` make target.
3. Add a coverage floor once suite coverage is measured.

## Pointers

- Architecture + commands: `CLAUDE.md`.
- Public API surface: `src/promptfw/__init__.py` (`__all__`).
- Changelog: `CHANGELOG.md` (Keep a Changelog).
