"""Core data models for promptfw."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


def _auto_token_count(text: str) -> int:
    """Return tiktoken token count if available, else 0 (no estimate)."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return 0


# Valid values for PromptTemplate.response_format / RenderedPrompt.response_format.
# Aligned with OpenAI/LiteLLM response_format parameter.
VALID_RESPONSE_FORMATS: frozenset[str] = frozenset({"json_object", "json_schema", "text"})


class TemplateLayer(str, Enum):
    SYSTEM = "system"
    FORMAT = "format"
    CONTEXT = "context"
    CONTEXT_PROJECT = "context_project"
    CONTEXT_CHAPTER = "context_chapter"
    CONTEXT_SCENE = "context_scene"
    TASK = "task"
    FEW_SHOT = "few_shot"


# Layers rendered into the user prompt (order matters for render_stack).
USER_LAYERS: tuple[TemplateLayer, ...] = (
    TemplateLayer.CONTEXT,
    TemplateLayer.CONTEXT_PROJECT,
    TemplateLayer.CONTEXT_CHAPTER,
    TemplateLayer.CONTEXT_SCENE,
    TemplateLayer.TASK,
)


@dataclass
class PromptTemplate:
    """A single prompt template with metadata."""

    id: str
    layer: TemplateLayer
    template: str
    variables: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    cacheable: bool = False
    tokens_estimate: int = 0
    format_type: str | None = None
    phase: str | None = None
    task: str | None = None
    few_shot_examples: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] | None = None
    response_format: Literal["json_object", "json_schema", "text"] | None = None

    def __post_init__(self) -> None:
        """Auto-calculate tokens_estimate from template if not set and tiktoken available."""
        if self.tokens_estimate == 0 and self.template:
            self.tokens_estimate = _auto_token_count(self.template)


@dataclass
class RenderedPrompt:
    """The result of rendering a prompt stack for an LLM call."""

    system: str
    user: str
    estimated_tokens: int = 0
    cache_breakpoints: list[int] = field(default_factory=list)
    few_shot_messages: list[dict[str, str]] = field(default_factory=list)
    output_schema: dict[str, Any] | None = None
    response_format: Literal["json_object", "json_schema", "text"] | None = None
