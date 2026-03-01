"""
Template registry with wildcard lookup, version-pinning, and optional hot-reload.

New in 0.2.0:
- Strict field validation on YAML load (clear error messages on bad templates)
- Version-pinning: stack.render("story.task@1.2.0", ctx)
- Hot-reload: registry.enable_hot_reload() watches directory for YAML changes
"""

from __future__ import annotations

import logging
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from promptfw.exceptions import TemplateNotFoundError
from promptfw.schema import PromptTemplate, TemplateLayer

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """
    Loads and manages prompt templates.
    Supports wildcard lookups: "roman.*.scene_generation"
    """

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    @classmethod
    def from_directory(cls, templates_dir: Path) -> "TemplateRegistry":
        """Load all YAML templates from a directory tree with field validation."""
        registry = cls()
        registry._templates_dir = Path(templates_dir)
        try:
            import yaml
        except ImportError as e:
            raise ImportError(
                "PyYAML is required to load templates from directory. "
                "Install with: pip install pyyaml"
            ) from e

        for yaml_file in Path(templates_dir).rglob("*.yaml"):
            registry._load_yaml_file(yaml_file, yaml)

        return registry

    def _load_yaml_file(self, yaml_file: Path, yaml=None) -> None:
        """Load and validate a single YAML template file."""
        if yaml is None:
            import yaml as _yaml
            yaml = _yaml
        try:
            with open(yaml_file) as f:
                data: dict[str, Any] = yaml.safe_load(f)
            if not data:
                return
            required = {"id", "layer", "template"}
            missing = required - set(data.keys())
            if missing:
                logger.warning(
                    "Skipping %s — missing required fields: %s", yaml_file.name, missing
                )
                return
            data["layer"] = TemplateLayer(data["layer"])
            tmpl = PromptTemplate(**data)
            self.register(tmpl)
        except Exception as e:
            logger.error("Failed to load template %s: %s", yaml_file, e)

    def register(self, template: PromptTemplate) -> None:
        """Register a template (overwrites existing with same id)."""
        self._templates[template.id] = template
        # also store by id@version for pinned lookups
        versioned_key = f"{template.id}@{template.version}"
        self._templates[versioned_key] = template

    def get(self, pattern: str) -> PromptTemplate:
        """
        Get template by exact ID, wildcard pattern, or version-pinned ID.

        Examples::

            registry.get("story.task.write")          # exact
            registry.get("story.*.write")             # wildcard
            registry.get("story.task.write@1.2.0")   # version-pinned
        """
        if pattern in self._templates:
            return self._templates[pattern]

        matches = [t for tid, t in self._templates.items() if fnmatch(tid, pattern)]
        if not matches:
            raise TemplateNotFoundError(pattern)

        # Sort by specificity: prefer the template whose ID most closely matches
        # the pattern. Fewer wildcard segments in the pattern = more specific match.
        # Tiebreak: longer (more specific) IDs win.
        wildcard_count = pattern.count("*")
        matches.sort(key=lambda t: (-len(t.id.replace("*", "")), wildcard_count))
        return matches[0]

    def _iter_base(self):
        """Iterate only over base (non-versioned) templates."""
        return (t for k, t in self._templates.items() if "@" not in k)

    def list_all(self) -> list[PromptTemplate]:
        return list(self._iter_base())

    def list_by_layer(self, layer: TemplateLayer) -> list[PromptTemplate]:
        return [t for t in self._iter_base() if t.layer == layer]

    def list_by_format(self, format_type: str) -> list[PromptTemplate]:
        return [t for t in self._iter_base() if t.format_type == format_type]

    def reload(self) -> None:
        """Reload all templates from disk (clears cache first)."""
        if not hasattr(self, "_templates_dir") or not self._templates_dir:
            logger.warning("reload() called but no templates_dir set")
            return
        import yaml
        self._templates.clear()
        for yaml_file in self._templates_dir.rglob("*.yaml"):
            self._load_yaml_file(yaml_file, yaml)
        logger.info("Registry reloaded — %d templates", len(self))

    def enable_hot_reload(self) -> None:
        """
        Enable file-system hot-reload via watchdog (dev mode).

        Requires: pip install watchdog
        """
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError as e:
            raise ImportError(
                "watchdog is required for hot-reload. Install with: pip install watchdog"
            ) from e

        registry_ref = self

        class _Handler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith(".yaml"):
                    logger.info("Hot-reload: %s changed", event.src_path)
                    registry_ref.reload()

            def on_created(self, event):
                if not event.is_directory and event.src_path.endswith(".yaml"):
                    logger.info("Hot-reload: new template %s", event.src_path)
                    registry_ref.reload()

        observer = Observer()
        observer.schedule(_Handler(), str(self._templates_dir), recursive=True)
        observer.daemon = True
        observer.start()
        logger.info("Hot-reload enabled for %s", self._templates_dir)

    def __len__(self) -> int:
        # exclude versioned keys from count
        return sum(1 for k in self._templates if "@" not in k)
