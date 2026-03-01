"""
promptfw — Prompt Template Framework

5-layer Jinja2 template engine for LLM applications.
"""

__version__ = "0.5.1"

from promptfw.exceptions import LLMResponseError, TemplateNotFoundError, TemplateRenderError
from promptfw.schema import (
    VALID_RESPONSE_FORMATS,
    PromptTemplate,
    RenderedPrompt,
    TemplateLayer,
    USER_LAYERS,
)
from promptfw.registry import TemplateRegistry
from promptfw.django_registry import DjangoTemplateRegistry, BFAGENT_FIELD_MAP
from promptfw.renderer import PromptRenderer
from promptfw.stack import PromptStack
from promptfw.planning import PLANNING_TEMPLATES, get_planning_stack
from promptfw.parsing import (
    extract_json,
    extract_json_list,
    extract_json_strict,
    extract_field,
)
from promptfw.writing import WRITING_TEMPLATES, get_writing_stack
from promptfw.lektorat import LEKTORAT_TEMPLATES, get_lektorat_stack

__all__ = [
    "PromptStack",
    "PromptTemplate",
    "RenderedPrompt",
    "TemplateLayer",
    "TemplateRegistry",
    "DjangoTemplateRegistry",
    "BFAGENT_FIELD_MAP",
    "PromptRenderer",
    "TemplateNotFoundError",
    "TemplateRenderError",
    "LLMResponseError",
    "VALID_RESPONSE_FORMATS",
    "USER_LAYERS",
    "get_planning_stack",
    "PLANNING_TEMPLATES",
    "extract_json",
    "extract_json_list",
    "extract_json_strict",
    "extract_field",
    "get_writing_stack",
    "WRITING_TEMPLATES",
    "get_lektorat_stack",
    "LEKTORAT_TEMPLATES",
    "__version__",
]
