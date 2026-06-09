"""
DBPromptResolver — DB-driven prompt resolution without Django dependency.

Resolves prompts in three-tier priority:
  1. DB custom prompts (system_prompt + user_template from your model)
  2. promptfw stack (render_stack from template_prefix)
  3. Generic fallback (works for any format, no hardcoding)

Usage (in any Django app)::

    from promptfw.db_resolver import DBPromptResolver

    resolver = DBPromptResolver(planning_stack)

    def my_loader(slug: str) -> dict:
        from apps.projects.models import ContentTypeLookup
        ct = ContentTypeLookup.objects.filter(slug=slug).only(
            "planning_action_code",
            "planning_prompt_template",
            "planning_system_prompt",
            "planning_user_template",
        ).first()
        if ct:
            return {
                "action_code": ct.planning_action_code or "planning_novel",
                "template_prefix": ct.planning_prompt_template or slug,
                "system_prompt": ct.planning_system_prompt or "",
                "user_template": ct.planning_user_template or "",
            }
        return None  # triggers fallback

    messages = resolver.resolve(
        slug="screenplay",
        loader_fn=my_loader,
        context={"title": "...", "genre": "...", "description": "..."},
    )
    # Pass messages directly to aifw.service.sync_completion(action_code, messages)

Design principles:
- NO Django import — pure Python, works in any framework
- loader_fn is injected by the caller (inversion of control)
- Deterministic fallback chain: DB > promptfw > generic
- Thread-safe (no mutable state)
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from promptfw.stack import PromptStack

logger = logging.getLogger(__name__)

_GENERIC_SYSTEM = (
    "Du bist ein erfahrener Autor und Lektor. Antworte praezise und kreativ auf Deutsch."
)
_GENERIC_USER = (
    "Erstelle die Planungsgrundlagen fuer folgendes Projekt:\n\n{context}\n\n"
    "Antworte als JSON mit den Feldern: "
    "premise (2-3 Saetze), themes (Liste), logline (1 Satz)."
)


class DBPromptResolver:
    """
    Resolves LLM messages from DB config + promptfw stack, Django-free.

    Args:
        stack:       Pre-built PromptStack (e.g. get_planning_stack()).
        default_action_code: Fallback action_code when DB has none.
        default_template_prefix: Fallback prefix when DB has none (e.g. 'roman').
    """

    def __init__(
        self,
        stack: PromptStack,
        default_action_code: str = "planning_novel",
        default_template_prefix: str = "roman",
    ) -> None:
        self._stack = stack
        self._default_action_code = default_action_code
        self._default_template_prefix = default_template_prefix

    def load_config(
        self,
        slug: str,
        loader_fn: Callable[[str], dict | None],
    ) -> dict:
        """
        Load planning config via injected loader_fn.

        loader_fn(slug) must return a dict with keys:
            action_code, template_prefix, system_prompt, user_template
        or None to trigger defaults.

        Never raises — falls back to safe defaults.
        """
        try:
            cfg = loader_fn(slug)
            if cfg:
                return {
                    "action_code": cfg.get("action_code") or self._default_action_code,
                    "template_prefix": cfg.get("template_prefix") or slug,
                    "system_prompt": cfg.get("system_prompt") or "",
                    "user_template": cfg.get("user_template") or "",
                }
        except Exception as exc:
            logger.warning("DBPromptResolver loader_fn failed for slug=%r: %s", slug, exc)

        logger.warning(
            "No DB config for slug=%r — using defaults (action_code=%s, prefix=%s)",
            slug,
            self._default_action_code,
            self._default_template_prefix,
        )
        return {
            "action_code": self._default_action_code,
            "template_prefix": self._default_template_prefix,
            "system_prompt": "",
            "user_template": "",
        }

    def build_messages(
        self,
        cfg: dict,
        context: dict[str, Any],
    ) -> list[dict[str, str]]:
        """
        Build OpenAI-compatible messages list from config + render context.

        Priority:
          1. DB custom: cfg[system_prompt] + cfg[user_template]
          2. promptfw stack: render_stack([prefix.system.planning, prefix.task.planning])
          3. Generic fallback with context string

        Args:
            cfg:     Result of load_config().
            context: Render context dict with keys like title, genre, description, context.

        Returns:
            List of {"role": ..., "content": ...} dicts.
        """
        # 1. DB custom prompts (both must be set)
        if cfg["system_prompt"] and cfg["user_template"]:
            try:
                user_msg = cfg["user_template"].format(**context)
            except KeyError:
                user_msg = cfg["user_template"]
            return [
                {"role": "system", "content": cfg["system_prompt"]},
                {"role": "user", "content": user_msg},
            ]

        # 2. promptfw stack
        prefix = cfg["template_prefix"]
        try:
            rendered = self._stack.render_stack(
                [f"{prefix}.system.planning", f"{prefix}.task.planning"],
                context=context,
            )
            system_content = cfg["system_prompt"] or rendered.system
            return [
                {"role": "system", "content": system_content},
                {"role": "user", "content": rendered.user},
            ]
        except Exception as exc:
            logger.warning(
                "promptfw render failed for prefix=%r (%s) — using generic fallback",
                prefix,
                exc,
            )

        # 3. Generic fallback
        ctx_str = context.get("context") or context.get("description") or str(context)
        return [
            {"role": "system", "content": cfg["system_prompt"] or _GENERIC_SYSTEM},
            {"role": "user", "content": _GENERIC_USER.format(context=ctx_str)},
        ]

    def resolve(
        self,
        slug: str,
        loader_fn: Callable[[str], dict | None],
        context: dict[str, Any],
    ) -> tuple[str, list[dict[str, str]]]:
        """
        Full resolution: load config + build messages in one call.

        Returns:
            (action_code, messages) tuple ready for aifw.service.sync_completion.

        Example::

            action_code, messages = resolver.resolve("screenplay", my_loader, ctx)
            result = sync_completion(action_code, messages)
        """
        cfg = self.load_config(slug, loader_fn)
        messages = self.build_messages(cfg, context)
        return cfg["action_code"], messages
