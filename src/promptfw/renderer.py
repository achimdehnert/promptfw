"""Jinja2-based prompt renderer with 4-layer stack support."""

from __future__ import annotations

from typing import Any

from jinja2 import BaseLoader, Environment, StrictUndefined, UndefinedError

from promptfw.exceptions import TemplateRenderError
from promptfw.schema import PromptTemplate, RenderedPrompt, TemplateLayer


class PromptRenderer:
    """
    Renders 4-layer prompt stacks from templates + runtime context.

    Layer order (bottom to top):
      SYSTEM → FORMAT → CONTEXT → TASK

    SYSTEM and FORMAT layers are rendered into system prompt (cacheable).
    CONTEXT and TASK layers are rendered into user prompt (dynamic).
    """

    def __init__(self) -> None:
        self._jinja = Environment(
            loader=BaseLoader(),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_template(self, template: PromptTemplate, context: dict[str, Any]) -> str:
        """Render a single template with the given context variables."""
        try:
            tmpl = self._jinja.from_string(template.template)
            return tmpl.render(**context)
        except UndefinedError as e:
            raise TemplateRenderError(template.id, str(e)) from e
        except Exception as e:
            raise TemplateRenderError(template.id, str(e)) from e

    def render_stack(
        self,
        templates: list[PromptTemplate],
        context: dict[str, Any],
    ) -> RenderedPrompt:
        """
        Render a list of templates into a RenderedPrompt.

        SYSTEM + FORMAT → system prompt (joined, cacheable)
        CONTEXT + TASK + FEW_SHOT → user prompt (joined)
        """
        system_parts: list[str] = []
        user_parts: list[str] = []
        cache_breakpoints: list[int] = []
        system_char_count = 0

        for tmpl in templates:
            rendered = self.render_template(tmpl, context)
            if not rendered.strip():
                continue

            if tmpl.layer in (TemplateLayer.SYSTEM, TemplateLayer.FORMAT):
                system_parts.append(rendered)
                if tmpl.cacheable:
                    system_char_count += len(rendered)
                    cache_breakpoints.append(system_char_count)
            else:
                user_parts.append(rendered)

        system_prompt = "\n\n".join(system_parts)
        user_prompt = "\n\n".join(user_parts)

        estimated_tokens = self._estimate_tokens(system_prompt + user_prompt)

        return RenderedPrompt(
            system=system_prompt,
            user=user_prompt,
            estimated_tokens=estimated_tokens,
            cache_breakpoints=cache_breakpoints,
        )

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate — 1 token ≈ 4 chars. Use tiktoken for accuracy."""
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except ImportError:
            return len(text) // 4
