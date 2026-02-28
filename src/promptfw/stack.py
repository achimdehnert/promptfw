"""
PromptStack — main façade for promptfw.

Usage:
    stack = PromptStack()
    stack.register(PromptTemplate(id="greet.task", layer=TemplateLayer.TASK,
                                  template="Say hello to {{ name }}",
                                  variables=["name"]))
    rendered = stack.render("greet.task", {"name": "Alice"})
    # rendered.system, rendered.user
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from promptfw.registry import TemplateRegistry
from promptfw.renderer import PromptRenderer
from promptfw.schema import PromptTemplate, RenderedPrompt


class PromptStack:
    """Main entry point for building and rendering prompt stacks."""

    def __init__(
        self,
        registry: TemplateRegistry | None = None,
        renderer: PromptRenderer | None = None,
    ) -> None:
        self.registry = registry or TemplateRegistry()
        self.renderer = renderer or PromptRenderer()

    @classmethod
    def from_directory(cls, templates_dir: Path | str) -> "PromptStack":
        """Load all YAML templates from a directory and return a ready PromptStack."""
        registry = TemplateRegistry.from_directory(Path(templates_dir))
        return cls(registry=registry)

    def register(self, template: PromptTemplate) -> None:
        """Register a single template programmatically."""
        self.registry.register(template)

    def render(self, pattern: str, context: dict[str, Any]) -> RenderedPrompt:
        """
        Render a single template by ID/pattern with the given context.

        Returns a RenderedPrompt with .system and .user strings.
        """
        template = self.registry.get(pattern)
        return self.renderer.render_stack([template], context)

    def render_stack(
        self, patterns: list[str], context: dict[str, Any]
    ) -> RenderedPrompt:
        """
        Render multiple templates (in order) into a combined RenderedPrompt.

        Useful for building full 4-layer stacks:
            stack.render_stack(
                ["system.base", "format.roman", "context.scene", "task.write"],
                context
            )
        """
        templates = [self.registry.get(p) for p in patterns]
        return self.renderer.render_stack(templates, context)
