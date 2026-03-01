"""
promptfw — Prompt Template Framework

4-layer Jinja2 template engine for LLM applications.
"""

__version__ = "0.3.0"

from promptfw.exceptions import TemplateNotFoundError, TemplateRenderError
from promptfw.schema import PromptTemplate, RenderedPrompt, TemplateLayer
from promptfw.registry import TemplateRegistry
from promptfw.renderer import PromptRenderer
from promptfw.stack import PromptStack
from promptfw.planning import PLANNING_TEMPLATES, get_planning_stack
from promptfw.parsing import extract_json, extract_json_list, extract_json_strict

__all__ = [
    "PromptStack",
    "PromptTemplate",
    "RenderedPrompt",
    "TemplateLayer",
    "TemplateRegistry",
    "PromptRenderer",
    "TemplateNotFoundError",
    "TemplateRenderError",
    "get_planning_stack",
    "PLANNING_TEMPLATES",
    "extract_json",
    "extract_json_list",
    "extract_json_strict",
    "__version__",
]
