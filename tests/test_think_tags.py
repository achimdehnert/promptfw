"""Tests for <think> tag stripping in promptfw.parsing."""
import pytest

from promptfw.parsing import (
    extract_json,
    extract_json_list,
    extract_json_strict,
    strip_reasoning_tags,
)


class TestStripReasoningTags:
    """Tests for strip_reasoning_tags()."""

    def test_strips_think_tags(self):
        text = '<think>\nLet me reason...\n</think>\n{"key": "value"}'
        assert strip_reasoning_tags(text) == '{"key": "value"}'

    def test_strips_reasoning_tags(self):
        text = '<reasoning>\nStep 1...\n</reasoning>\nResult'
        assert strip_reasoning_tags(text) == 'Result'

    def test_strips_thought_tags(self):
        text = '<thought>Hmm...</thought>Answer'
        assert strip_reasoning_tags(text) == 'Answer'

    def test_case_insensitive(self):
        text = '<THINK>\nreasoning\n</THINK>\noutput'
        assert strip_reasoning_tags(text) == 'output'

    def test_no_tags_unchanged(self):
        text = '{"key": "value"}'
        assert strip_reasoning_tags(text) == text

    def test_empty_string(self):
        assert strip_reasoning_tags("") == ""

    def test_multiple_think_blocks(self):
        text = '<think>first</think>middle<think>second</think>end'
        assert strip_reasoning_tags(text) == 'middleend'


class TestExtractJsonWithThinkTags:
    """Verify extract_json handles <think> tags from reasoning models."""

    def test_json_after_think_block(self):
        text = '<think>\nLet me analyze...\n</think>\n{"verdict": "accept"}'
        result = extract_json(text)
        assert result == {"verdict": "accept"}

    def test_json_in_code_fence_after_think(self):
        text = (
            '<think>\nI need to format as JSON...\n</think>\n'
            '```json\n{"score": 8}\n```'
        )
        result = extract_json(text)
        assert result == {"score": 8}

    def test_json_list_after_think_block(self):
        text = '<think>\nListing findings...\n</think>\n[{"id": 1}, {"id": 2}]'
        result = extract_json_list(text)
        assert len(result) == 2
        assert result[0]["id"] == 1

    def test_json_strict_after_think_block(self):
        text = '<think>\nProcessing...\n</think>\n{"status": "ok"}'
        result = extract_json_strict(text)
        assert result == {"status": "ok"}

    def test_think_block_containing_json(self):
        """JSON inside <think> should be ignored, only final output matters."""
        text = (
            '<think>\nIntermediate: {"wrong": true}\n</think>\n'
            '{"correct": true}'
        )
        result = extract_json(text)
        assert result == {"correct": True}

    def test_no_json_after_think_returns_none(self):
        text = '<think>\nJust reasoning, no JSON output.\n</think>\nPlain text.'
        result = extract_json(text)
        assert result is None
