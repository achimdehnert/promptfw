"""
JSON parsing utilities for LLM responses.

LLM responses often contain JSON embedded in markdown code fences or as raw text.
These utilities extract and parse JSON reliably without requiring callers to
duplicate regex logic.

Usage::

    from promptfw.parsing import extract_json, extract_json_list, extract_json_strict

    data = extract_json(llm_response)          # dict | None
    items = extract_json_list(llm_response)    # list (empty if not found)
    data = extract_json_strict(llm_response)   # dict or raises LLMResponseError
"""

from __future__ import annotations

import json
import re
from typing import Any

from promptfw.exceptions import LLMResponseError

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
