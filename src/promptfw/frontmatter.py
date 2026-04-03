"""YAML frontmatter template loader for .jinja2 files.

Handles templates with YAML frontmatter (system/user roles) commonly used
in Django projects.  This is the SSoT for frontmatter parsing — consuming
repos should NOT reimplement this logic.

Template format::

    ---
    system: |
      Du bist ein {{ role }}.
    user: |
      Analysiere: {{ text }}
    ---

Usage::

    from promptfw.frontmatter import render_frontmatter_file

    messages = render_frontmatter_file(
        "path/to/template.jinja2",
        role="Experte",
        text="Lorem ipsum",
    )
    # [{"role": "system", "content": "Du bist ein Experte."},
    #  {"role": "user", "content": "Analysiere: Lorem ipsum"}]
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def render_frontmatter_file(
    file_path: str | Path,
    **context: Any,
) -> list[dict[str, str]]:
    """Load a .jinja2 file with YAML frontmatter and render to messages.

    Args:
        file_path: Path to .jinja2 template file with YAML frontmatter.
        **context: Variables to render into the template.

    Returns:
        List of message dicts: [{"role": "system", "content": "..."}, ...]

    Raises:
        FileNotFoundError: If the template file doesn't exist.
        ValueError: If the file has no valid YAML frontmatter.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")

    content = path.read_text(encoding="utf-8")
    return render_frontmatter_string(content, **context)


def render_frontmatter_string(
    content: str,
    **context: Any,
) -> list[dict[str, str]]:
    """Parse YAML frontmatter from a string and render to messages.

    Args:
        content: Template string with YAML frontmatter between --- markers.
        **context: Variables to render into the template.

    Returns:
        List of message dicts.

    Raises:
        ValueError: If no valid YAML frontmatter found.
    """
    try:
        import yaml
    except ImportError as e:
        raise ImportError(
            "PyYAML is required for frontmatter templates. "
            "Install with: pip install pyyaml"
        ) from e

    try:
        from jinja2 import Template
    except ImportError as e:
        raise ImportError(
            "Jinja2 is required for frontmatter templates. "
            "Install with: pip install jinja2"
        ) from e

    if not content.startswith("---"):
        raise ValueError("Template must start with YAML frontmatter (---)")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Invalid frontmatter: expected --- ... --- format")

    frontmatter = yaml.safe_load(parts[1])
    if not isinstance(frontmatter, dict):
        raise ValueError(
            f"Frontmatter must be a YAML dict, got {type(frontmatter).__name__}"
        )

    messages: list[dict[str, str]] = []

    for role in ("system", "user", "assistant"):
        if role in frontmatter:
            tpl = Template(str(frontmatter[role]))
            rendered = tpl.render(**context).strip()
            if rendered:
                messages.append({"role": role, "content": rendered})

    return messages
