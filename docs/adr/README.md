# Architecture Decision Records — promptfw

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](ADR-001-four-layer-prompt-stack.md) | Five-Layer Prompt Stack Architecture | Accepted |
| [ADR-002](ADR-002-yaml-registry-vs-db-registry.md) | YAML Registry vs. DB Registry | Accepted |
| [ADR-003](ADR-003-extension-roadmap.md) | Extension Roadmap (writing, lektorat, parsing, output_schema) | Accepted (implemented) |

## External ADRs referenced by this repo

Some modules (notably `src/promptfw/contrib/django/`) reference **ADR-146
(DB-backed / hub prompt management)**. That ADR is **platform-level**, not local:

- Canonical: `platform/docs/adr/ADR-146-hub-prompt-management.md`

If you followed an `ADR-146` reference in a docstring and landed here, that is why —
it is intentionally maintained at the platform level, not duplicated into this package.
