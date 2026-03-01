"""
Jinja2-based prompt renderer with 5-layer stack support.

New in 0.2.0:
- Few-shot examples rendered from PromptTemplate.few_shot_examples
- render_to_messages() — direct LiteLLM/OpenAI messages list output

New in 0.5.0:
- Context sub-layers: CONTEXT_PROJECT, CONTEXT_CHAPTER, CONTEXT_SCENE
- Automatic layer ordering in render_stack (callers need not sort)
"""

from __future__ import annotations

from typing import Any

from jinja2 import BaseLoader, Environment, StrictUndefined, UndefinedError

from promptfw.exceptions import TemplateRenderError
from promptfw.schema import PromptTemplate, RenderedPrompt, TemplateLayer, USER_LAYERS


class PromptRenderer:
    """
    Renders 5-layer prompt stacks from templates + runtime context.

    Layer order (bottom to top):
      SYSTEM → FORMAT → CONTEXT → CONTEXT_PROJECT → CONTEXT_CHAPTER
      → CONTEXT_SCENE → TASK → FEW_SHOT

    SYSTEM and FORMAT layers → system prompt (stable, cacheable)
    CONTEXT*, TASK, FEW_SHOT  → user prompt (dynamic)
    """

    def __init__(self) -> None:
        self._jinja = Environment(
            loader=BaseLoader(),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_template(self, template: PromptTemplate, context: dict[str, Any]) -> str:
        """Render a single template with the given context variables.

        Variables declared in ``template.variables`` that are absent from ``context``
        are pre-filled with ``None`` so that ``{% if var %}`` guards work correctly
        without raising ``UndefinedError``.
        """
        try:
            merged = {v: None for v in template.variables}
            merged.update(context)
            tmpl = self._jinja.from_string(template.template)
            return tmpl.render(**merged)
        except UndefinedError as e:
            raise TemplateRenderError(template.id, str(e)) from e
        except Exception as e:
            raise TemplateRenderError(template.id, str(e)) from e

    def _render_few_shot(self, template: PromptTemplate) -> str:
        """Render few-shot examples from template.few_shot_examples list."""
        if not template.few_shot_examples:
            return ""
        parts = []
        for ex in template.few_shot_examples:
            user_text = ex.get("user", ex.get("input", ""))
            assistant_text = ex.get("assistant", ex.get("output", ""))
            if user_text and assistant_text:
                parts.append(f"User: {user_text}\nAssistant: {assistant_text}")
        return "\n\n".join(parts)

    def render_stack(
        self,
        templates: list[PromptTemplate],
        context: dict[str, Any],
    ) -> RenderedPrompt:
        """
        Render a list of templates into a RenderedPrompt.

        Templates are automatically sorted by canonical layer order:
        SYSTEM/FORMAT → system prompt; CONTEXT*/TASK → user prompt; FEW_SHOT last.
        """
        system_parts: list[str] = []
        user_parts: list[str] = []
        few_shot_messages: list[dict[str, str]] = []
        cache_breakpoints: list[int] = []
        system_char_count = 0
        output_schema: dict[str, Any] | None = None
        response_format: str | None = None

        # Sort templates by canonical layer order so callers don't have to.
        # FEW_SHOT always appended last regardless of registration order.
        _system_layers = (TemplateLayer.SYSTEM, TemplateLayer.FORMAT)
        _few_shot = TemplateLayer.FEW_SHOT
        ordered = sorted(
            templates,
            key=lambda t: (
                0 if t.layer in _system_layers else
                1 if t.layer in USER_LAYERS else
                2  # FEW_SHOT
            ),
        )

        for tmpl in ordered:
            if tmpl.layer == _few_shot:
                for ex in tmpl.few_shot_examples:
                    user_text = ex.get("user", ex.get("input", ""))
                    assistant_text = ex.get("assistant", ex.get("output", ""))
                    if user_text:
                        few_shot_messages.append({"role": "user", "content": user_text})
                    if assistant_text:
                        few_shot_messages.append(
                            {"role": "assistant", "content": assistant_text}
                        )
                continue

            rendered = self.render_template(tmpl, context)
            if not rendered.strip():
                continue

            if tmpl.layer in _system_layers:
                system_parts.append(rendered)
                if tmpl.cacheable:
                    system_char_count += len(rendered)
                    cache_breakpoints.append(system_char_count)
            else:
                user_parts.append(rendered)

            # Only TASK-layer templates propagate output_schema / response_format.
            # SYSTEM/FORMAT templates must not override the TASK's response contract.
            if tmpl.layer == TemplateLayer.TASK:
                if tmpl.output_schema is not None:
                    output_schema = tmpl.output_schema
                if tmpl.response_format is not None:
                    response_format = tmpl.response_format

        system_prompt = "\n\n".join(system_parts)
        user_prompt = "\n\n".join(user_parts)
        estimated_tokens = self._estimate_tokens(system_prompt + user_prompt)

        return RenderedPrompt(
            system=system_prompt,
            user=user_prompt,
            estimated_tokens=estimated_tokens,
            cache_breakpoints=cache_breakpoints,
            few_shot_messages=few_shot_messages,
            output_schema=output_schema,
            response_format=response_format,
        )

    def render_to_messages(
        self,
        templates: list[PromptTemplate],
        context: dict[str, Any],
    ) -> list[dict[str, str]]:
        """
        Render stack directly into OpenAI/LiteLLM messages format.

        Returns::

            [
                {"role": "system",    "content": "..."},
                {"role": "user",      "content": "few-shot example user"},
                {"role": "assistant", "content": "few-shot example assistant"},
                {"role": "user",      "content": "actual task prompt"},
            ]
        """
        rendered = self.render_stack(templates, context)
        messages: list[dict[str, str]] = []

        if rendered.system:
            messages.append({"role": "system", "content": rendered.system})

        messages.extend(rendered.few_shot_messages)

        if rendered.user:
            messages.append({"role": "user", "content": rendered.user})

        return messages

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate — 1 token ≈ 4 chars. Use tiktoken for accuracy."""
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except ImportError:
            return len(text) // 4
