# promptfw — Prompt Template Framework

4-layer Jinja2 template engine for LLM applications.

## Installation

```bash
pip install promptfw
# With token counting:
pip install promptfw[tiktoken]
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
# rendered.user    →  user prompt   (CONTEXT + TASK layers)
```

## 4-Layer Stack

```
SYSTEM   → Role & base behaviour  (stable, cacheable)
FORMAT   → Format-specific rules   (stable, cacheable)
CONTEXT  → Runtime context         (dynamic: characters, world, prior text)
TASK     → Concrete task           (dynamic: what to write now)
```

```python
rendered = stack.render_stack(
    ["system.base", "format.roman", "context.scene", "task.write_scene"],
    context={
        "role": "professional author",
        "style_rules": "Show don't tell",
        "characters": "Alice, Bob",
        "current_scene": "The forest at night",
        "task": "Write scene 3.2",
    }
)
```

## Load Templates from YAML

```python
# templates/story/task/write_scene.yaml
# id: story.task.write_scene
# layer: task
# template: |
#   Write scene {{ scene_id }}: {{ scene_description }}
#   Characters: {{ characters }}

stack = PromptStack.from_directory("templates/")
rendered = stack.render("story.task.write_scene", context)
```

## Wildcard Lookup

```python
# Matches "roman.first_draft.scene_generation"
template = stack.registry.get("roman.*.scene_generation")
```
