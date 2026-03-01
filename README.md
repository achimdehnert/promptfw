# promptfw — Prompt Template Framework

5-layer Jinja2 template engine for LLM applications.

[![PyPI](https://img.shields.io/pypi/v/promptfw)](https://pypi.org/project/promptfw/)
[![Python](https://img.shields.io/pypi/pyversions/promptfw)](https://pypi.org/project/promptfw/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install promptfw
# With accurate token counting:
pip install promptfw[tiktoken]
# All optional dependencies:
pip install promptfw[all]
```

## Quick Start

```python
from promptfw import PromptStack, PromptTemplate, TemplateLayer

stack = PromptStack()
stack.register(PromptTemplate(
    id="story.task.write",
    layer=TemplateLayer.TASK,
    template="Write a {{ genre }} story about {{ topic }} in {{ words }} words.",
    variables=["genre", "topic", "words"],
))

rendered = stack.render("story.task.write", {
    "genre": "fantasy",
    "topic": "a dragon who learns to code",
    "words": 500,
})
# rendered.system  →  system prompt (SYSTEM + FORMAT layers)
# rendered.user    →  user prompt   (CONTEXT* + TASK layers)
```

## 5-Layer Stack

```
SYSTEM           → Role & base behaviour      (stable, cacheable)
FORMAT           → Format-specific rules       (stable, cacheable)
CONTEXT          → Generic runtime context     (dynamic)
CONTEXT_PROJECT  → Project-level context       (dynamic, v0.5.0)
CONTEXT_CHAPTER  → Chapter-level context       (dynamic, v0.5.0)
CONTEXT_SCENE    → Scene-level context         (dynamic, v0.5.0)
TASK             → Concrete task               (dynamic)
FEW_SHOT         → Examples                    (appended last)
```

```python
rendered = stack.render_stack(
    ["system.base", "format.roman", "context.project", "context.scene", "task.write_scene"],
    context={
        "role": "professional author",
        "project": "The Iron Throne",
        "current_scene": "The forest at night",
        "characters": "Alice, Bob",
    }
)
```

## Load Templates from YAML

```yaml
# templates/story/task/write_scene.yaml
id: story.task.write_scene
layer: task
template: |
  Write scene {{ scene_id }}: {{ scene_description }}
  Characters: {{ characters }}
```

```python
stack = PromptStack.from_directory("templates/")
rendered = stack.render("story.task.write_scene", context)
```

## LiteLLM / OpenAI Direct Output

```python
# render_to_messages() returns [{"role": ..., "content": ...}, ...] directly
messages = stack.render_to_messages(
    ["system.base", "few_shot.examples", "task.write"],
    context={...},
)
# Pass directly to litellm.completion() or openai.chat.completions.create()
```

## Format-Aware Filtering

```python
# for_format() returns a new stack with only matching templates.
# Templates with format_type=None are always included (format-agnostic).
stack = get_planning_stack()
messages = stack.for_format("academic").render_to_messages(
    ["planning.system", "planning.task.premise"],
    context={...},
)
```

## Fallback Chains

```python
# render_with_fallback() tries patterns in order; first match wins.
result = stack.render_with_fallback(
    [
        "writing.task.write_chapter.roman",
        "writing.task.write_chapter",
        "writing.task.default",
    ],
    context={...},
)

# get_or_fallback() on the registry level:
template = registry.get_or_fallback([
    "chapter_writer_v2",
    "chapter_writer_v1",
    "chapter_writer_default",
])
```

## Wildcard Lookup & Version Pinning

```python
# Wildcard
template = stack.registry.get("roman.*.scene_generation")

# Version-pinned
rendered = stack.render_stack(
    ["system.base@1.0.0", "format.roman", "task.write@2.1.0"],
    context,
)
```

## Markdown Response Parsing

```python
from promptfw import extract_field, extract_json

# LLMs often respond with Markdown key:value text instead of JSON
text = "**Premise:** A blacksmith discovers magic.\n**Themes:** Identity, Power"
extract_field(text, "Premise")              # → "A blacksmith discovers magic."
extract_field(text, "Themes")               # → "Identity, Power"
extract_field(text, "Missing", default="")  # → ""

# JSON extraction from fenced blocks or raw text
data = extract_json(llm_response)           # dict | None
items = extract_json_list(llm_response)     # list
data = extract_json_strict(llm_response)    # dict or raises LLMResponseError
```

## Token Estimation

```python
# tokens_estimate is auto-calculated at construction time when tiktoken is installed
from promptfw import PromptTemplate, TemplateLayer

tmpl = PromptTemplate(
    id="task.write",
    layer=TemplateLayer.TASK,
    template="Write a short story about {{ topic }}.",
)
print(tmpl.tokens_estimate)  # e.g. 9 (via tiktoken cl100k_base)
```

## Django Integration

```python
from promptfw import DjangoTemplateRegistry

# Load from Django ORM queryset
registry = DjangoTemplateRegistry.from_queryset(
    PromptTemplateModel.objects.filter(is_active=True)
)
stack = PromptStack(registry=registry)
```

## Context Sub-Layers (v0.5.0)

For hierarchical document structures (book → chapter → scene):

```python
from promptfw import TemplateLayer, USER_LAYERS

# Available sub-layers (rendered in this order within user prompt):
# CONTEXT → CONTEXT_PROJECT → CONTEXT_CHAPTER → CONTEXT_SCENE → TASK

stack.render_stack(
    ["sys", "context.project", "context.chapter", "context.scene", "task"],
    context={...},
)
# render_stack auto-sorts to canonical order regardless of list order
```

## Hot Reload (dev mode)

```bash
pip install promptfw[hotreload]
```

```python
stack = PromptStack.from_directory("templates/")
stack.enable_hot_reload()  # watches for YAML changes
```

## Optional Dependencies

| Extra | Package | Feature |
|---|---|---|
| `tiktoken` | tiktoken≥0.6 | Accurate token counting |
| `hotreload` | watchdog≥4.0 | File-system hot reload |
| `django` | django≥4.2 | ORM queryset adapter |
| `all` | all above | Everything |
