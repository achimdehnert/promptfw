"""promptfw — Prompt Template Framework.

5-layer Jinja2 template engine for LLM applications: a registry of
``PromptTemplate`` objects (SYSTEM / FORMAT / CONTEXT* / TASK / FEW_SHOT layers)
that renders into system + user prompts or directly into OpenAI/LiteLLM message
lists. The public API is re-exported here; the implementation lives in submodules:

- ``promptfw.schema``           — ``PromptTemplate``, ``RenderedPrompt``, ``TemplateLayer``, ``USER_LAYERS``
- ``promptfw.registry``         — ``TemplateRegistry`` (wildcard lookup, version pinning, fallback chains)
- ``promptfw.renderer``         — ``PromptRenderer`` (Jinja2 rendering engine)
- ``promptfw.stack``            — ``PromptStack`` (high-level facade: register, render, render_to_messages)
- ``promptfw.parsing``          — ``extract_json``/``extract_field`` LLM-response parsers
- ``promptfw.frontmatter``      — render Markdown files/strings with YAML frontmatter
- ``promptfw.planning``         — ``get_planning_stack()`` + ``PLANNING_TEMPLATES``
- ``promptfw.writing``          — writing/academic/scientific stacks
- ``promptfw.lektorat``         — ``get_lektorat_stack()`` + ``LEKTORAT_TEMPLATES``
- ``promptfw.concept_analysis`` — ``get_concept_analysis_stack()`` + templates
- ``promptfw.db_resolver``      — ``DBPromptResolver`` (DB-backed template resolution)
- ``promptfw.django_registry``  — ``DjangoTemplateRegistry`` ORM adapter
- ``promptfw.contrib.django``   — optional Django app (models, admin, management commands)
- ``promptfw.exceptions``       — ``TemplateNotFoundError``, ``TemplateRenderError``, ``LLMResponseError``

``__version__`` is resolved from the installed package metadata.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("iil-promptfw")
except PackageNotFoundError:  # source checkout without an install
    __version__ = "0.0.0.dev0"

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
from promptfw.writing import (
    WRITING_TEMPLATES,
    get_writing_stack,
    get_academic_writing_stack,
    get_scientific_writing_stack,
)
from promptfw.lektorat import LEKTORAT_TEMPLATES, get_lektorat_stack
from promptfw.concept_analysis import CONCEPT_ANALYSIS_TEMPLATES, get_concept_analysis_stack
from promptfw.db_resolver import DBPromptResolver
from promptfw.frontmatter import render_frontmatter_file, render_frontmatter_string

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
    "get_academic_writing_stack",
    "get_scientific_writing_stack",
    "WRITING_TEMPLATES",
    "get_lektorat_stack",
    "LEKTORAT_TEMPLATES",
    "get_concept_analysis_stack",
    "CONCEPT_ANALYSIS_TEMPLATES",
    "DBPromptResolver",
    "render_frontmatter_file",
    "render_frontmatter_string",
    "__version__",
]
