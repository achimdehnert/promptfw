"""Core data models for promptfw."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TemplateLayer(str, Enum):
    SYSTEM = "system"
    FORMAT = "format"
    CONTEXT = "context"
    TASK = "task"
    FEW_SHOT = "few_shot"


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


@dataclass
class RenderedPrompt:
    """The result of rendering a prompt stack for an LLM call."""

    system: str
    user: str
    estimated_tokens: int = 0
    cache_breakpoints: list[int] = field(default_factory=list)
