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

from promptfw.exceptions import TemplateNotFoundError  # noqa: F401 re-exported
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

        Supports version-pinning::

            stack.render_stack(
                ["system.base@1.0.0", "format.roman", "task.write@2.1.0"],
                context
            )
        """
        templates = [self.registry.get(p) for p in patterns]
        return self.renderer.render_stack(templates, context)

    def render_to_messages(
        self, patterns: list[str], context: dict[str, Any]
    ) -> list[dict[str, str]]:
        """
        Render stack directly into OpenAI/LiteLLM messages list.

        Includes few-shot examples as interleaved user/assistant messages::

            messages = stack.render_to_messages(
                ["system.base", "few_shot.examples", "task.write"],
                context,
            )
            # Pass directly to aifw.completion() or litellm.completion()
        """
        templates = [self.registry.get(p) for p in patterns]
        return self.renderer.render_to_messages(templates, context)

    def render_with_fallback(
        self,
        patterns: list[str],
        context: dict[str, Any],
    ) -> RenderedPrompt:
        """
        Render the first matching template from an ordered fallback list.

        Tries each pattern in order; renders the first one found.
        Useful for progressive specificity::

            stack.render_with_fallback(
                [
                    "writing.task.write_chapter.roman",
                    "writing.task.write_chapter",
                    "writing.task.default",
                ],
                context={...},
            )

        Args:
            patterns: Ordered list of template IDs or wildcard patterns.
                      First match wins.
            context:  Jinja2 render context.

        Returns:
            RenderedPrompt from the first matching template.

        Raises:
            TemplateNotFoundError: If no pattern matches any registered template.
        """
        template = self.registry.get_or_fallback(patterns)
        return self.renderer.render_stack([template], context)

    def enable_hot_reload(self) -> None:
        """
        Enable YAML file-system hot-reload (dev mode only).

        Requires: pip install watchdog
        """
        self.registry.enable_hot_reload()
