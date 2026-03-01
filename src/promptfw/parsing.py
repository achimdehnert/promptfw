"""
JSON and Markdown parsing utilities for LLM responses.

LLM responses often contain JSON embedded in markdown code fences or as raw text.
Some LLMs respond with Markdown-structured key/value text instead of JSON.
These utilities extract and parse both formats reliably.

Usage::

    from promptfw.parsing import extract_json, extract_json_list, extract_json_strict
    from promptfw.parsing import extract_field

    data = extract_json(llm_response)          # dict | None
    items = extract_json_list(llm_response)    # list (empty if not found)
    data = extract_json_strict(llm_response)   # dict or raises LLMResponseError

    # Markdown field extraction (issue #8)
    text = "**Premise:** Eine Geschichte.\n**Themes:** Identität, Macht"
    extract_field(text, "Premise")             # → "Eine Geschichte."
    extract_field(text, "Missing", default="") # → ""
"""

from __future__ import annotations

import json
import re
from typing import Any

from promptfw.exceptions import LLMResponseError

# Matches **Field:**, Field:, ### Field patterns — case-insensitive.
# Group 1: field name, Group 2: value on same line (may be empty).
_FIELD_HEADER = re.compile(
    r"(?:^|\n)\s*(?:\*{1,2}|#{1,3}\s*)?"
    r"([\w][\w \-]{0,48}?)"
    r"(?:\*{1,2})?\s*:\s*(.*)",
    re.IGNORECASE,
)

# Ordered list of patterns tried in sequence — most specific first.
_OBJECT_PATTERNS = [
    re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE),
    re.compile(r"```\s*(\{.*?\})\s*```", re.DOTALL),
    re.compile(r"(?<!\[)(\{.*\})(?!\])", re.DOTALL),
]

_ARRAY_PATTERNS = [
    re.compile(r"```json\s*(\[.*?\])\s*```", re.DOTALL | re.IGNORECASE),
    re.compile(r"```\s*(\[.*?\])\s*```", re.DOTALL),
    re.compile(r"(\[.*\])", re.DOTALL),
]


def _try_patterns(text: str, patterns: list[re.Pattern]) -> Any | None:
    """Try each pattern in order; return parsed JSON on first valid match."""
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            candidate = match.group(1)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    return None


def extract_json(text: str) -> dict | None:
    """
    Extract the first JSON object from an LLM response string.

    Handles:
    - Markdown-fenced blocks: ```json { ... } ```
    - Plain fenced blocks:    ``` { ... } ```
    - Raw JSON objects anywhere in the text

    Returns ``None`` if no valid JSON object is found.
    """
    if not text or not text.strip():
        return None
    result = _try_patterns(text, _OBJECT_PATTERNS)
    if isinstance(result, dict):
        return result
    return None


def extract_json_list(text: str) -> list:
    """
    Extract the first JSON array from an LLM response string.

    Handles the same patterns as ``extract_json``.

    Returns an empty list if no valid JSON array is found.
    """
    if not text or not text.strip():
        return []
    result = _try_patterns(text, _ARRAY_PATTERNS)
    if isinstance(result, list):
        return result
    return []


def extract_json_strict(text: str) -> dict:
    """
    Extract the first JSON object from an LLM response or raise ``LLMResponseError``.

    Use this when a JSON response is required and absence should be treated as an error.

    Raises:
        LLMResponseError: If no valid JSON object is found in ``text``.
    """
    result = extract_json(text)
    if result is None:
        preview = text[:120].replace("\n", " ") if text else "<empty>"
        raise LLMResponseError(
            cause="No JSON object found in LLM response",
            preview=preview,
        )
    return result


def extract_field(
    text: str,
    field: str,
    default: Any = None,
) -> Any:
    """
    Extract a named field from a Markdown-structured LLM response.

    Handles common LLM output patterns:

    - ``**Field:** value``
    - ``Field: value``
    - ``### Field``  (value on next line or after colon)

    Matching is case-insensitive. The value runs until the next field
    header or end of string, and is stripped of leading/trailing whitespace.

    Args:
        text:    LLM response string to search.
        field:   Field name to look for (case-insensitive).
        default: Returned when the field is not found. Defaults to ``None``.

    Returns:
        Extracted string value, or ``default`` if not found.

    Examples::

        text = "**Premise:** Eine Geschichte.\\n**Themes:** Identität, Macht"
        extract_field(text, "Premise")            # → "Eine Geschichte."
        extract_field(text, "Themes")             # → "Identität, Macht"
        extract_field(text, "Missing", default="") # → ""
    """
    if not text or not text.strip():
        return default

    # Build a list of (start_pos, field_name, first_line_value) from all matches.
    entries: list[tuple[int, str, str]] = []
    for m in _FIELD_HEADER.finditer(text):
        entries.append((m.start(), m.group(1).strip(), m.group(2).strip()))

    # Find the target field (case-insensitive exact match).
    target = field.strip().lower()
    for idx, (pos, name, first_val) in enumerate(entries):
        if name.lower() != target:
            continue

        # Collect value: first_val + text until next field header.
        if idx + 1 < len(entries):
            next_pos = entries[idx + 1][0]
            between = text[pos:next_pos]
        else:
            between = text[pos:]

        # Re-extract cleanly: skip the header line, take remaining lines.
        lines = between.splitlines()
        # First line already parsed into first_val; collect continuation lines.
        continuation = "\n".join(lines[1:]).strip()
        value = (first_val + ("\n" + continuation if continuation else "")).strip()
        return value if value else default

    return default
