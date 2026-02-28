"""Template registry with wildcard lookup support."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from promptfw.exceptions import TemplateNotFoundError
from promptfw.schema import PromptTemplate, TemplateLayer


class TemplateRegistry:
    """
    Loads and manages prompt templates.
    Supports wildcard lookups: "roman.*.scene_generation"
    """

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    @classmethod
    def from_directory(cls, templates_dir: Path) -> "TemplateRegistry":
        """Load all YAML templates from a directory tree."""
        registry = cls()
        try:
            import yaml
        except ImportError as e:
            raise ImportError(
                "PyYAML is required to load templates from directory. "
                "Install with: pip install pyyaml"
            ) from e

        for yaml_file in Path(templates_dir).rglob("*.yaml"):
            with open(yaml_file) as f:
                data: dict[str, Any] = yaml.safe_load(f)
            if data and "id" in data and "layer" in data and "template" in data:
                data["layer"] = TemplateLayer(data["layer"])
                registry.register(PromptTemplate(**data))

        return registry

    def register(self, template: PromptTemplate) -> None:
        """Register a template (overwrites existing with same id)."""
        self._templates[template.id] = template

    def get(self, pattern: str) -> PromptTemplate:
        """
        Get template by exact ID or wildcard pattern.
        "roman.*.scene" matches "roman.first_draft.scene"
        """
        if pattern in self._templates:
            return self._templates[pattern]

        matches = [t for tid, t in self._templates.items() if fnmatch(tid, pattern)]
        if not matches:
            raise TemplateNotFoundError(pattern)

        matches.sort(key=lambda t: t.id.count("*"))
        return matches[0]

    def list_all(self) -> list[PromptTemplate]:
        return list(self._templates.values())

    def list_by_layer(self, layer: TemplateLayer) -> list[PromptTemplate]:
        return [t for t in self._templates.values() if t.layer == layer]

    def list_by_format(self, format_type: str) -> list[PromptTemplate]:
        return [t for t in self._templates.values() if t.format_type == format_type]

    def __len__(self) -> int:
        return len(self._templates)
