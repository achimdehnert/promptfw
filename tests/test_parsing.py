"""Tests for promptfw.parsing — JSON extraction utilities."""

import pytest

from promptfw.exceptions import LLMResponseError
from promptfw.parsing import extract_json, extract_json_list, extract_json_strict


class TestExtractJson:
    def test_should_extract_json_from_markdown_fenced_block(self):
        text = '```json\n{"key": "value", "count": 42}\n```'
        result = extract_json(text)
        assert result == {"key": "value", "count": 42}

    def test_should_extract_json_from_plain_fenced_block(self):
        text = '```\n{"key": "value"}\n```'
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_should_extract_raw_json_object_from_text(self):
        text = 'Here is the result:\n{"status": "ok", "score": 0.9}\nDone.'
        result = extract_json(text)
        assert result == {"status": "ok", "score": 0.9}

    def test_should_extract_nested_json_object(self):
        text = '{"outer": {"inner": [1, 2, 3]}, "flag": true}'
        result = extract_json(text)
        assert result == {"outer": {"inner": [1, 2, 3]}, "flag": True}

    def test_should_return_none_when_no_json_present(self):
        result = extract_json("This is plain text with no JSON.")
        assert result is None

    def test_should_return_none_for_empty_string(self):
        assert extract_json("") is None

    def test_should_return_none_for_whitespace_only(self):
        assert extract_json("   \n\t  ") is None

    def test_should_return_none_for_invalid_json(self):
        result = extract_json("```json\n{broken json}\n```")
        assert result is None

    def test_should_prefer_fenced_block_over_raw_json(self):
        text = 'raw: {"raw": true}\n```json\n{"fenced": true}\n```'
        result = extract_json(text)
        assert result == {"fenced": True}

    def test_should_handle_case_insensitive_json_fence(self):
        text = "```JSON\n{\"key\": \"val\"}\n```"
        result = extract_json(text)
        assert result == {"key": "val"}

    def test_should_return_none_for_json_array_input(self):
        result = extract_json('[{"item": 1}]')
        assert result is None


class TestExtractJsonList:
    def test_should_extract_list_from_markdown_fenced_block(self):
        text = '```json\n[{"name": "Alice"}, {"name": "Bob"}]\n```'
        result = extract_json_list(text)
        assert result == [{"name": "Alice"}, {"name": "Bob"}]

    def test_should_extract_raw_json_array_from_text(self):
        text = 'Characters found:\n[{"name": "Alice", "role": "protagonist"}]\nEnd.'
        result = extract_json_list(text)
        assert result == [{"name": "Alice", "role": "protagonist"}]

    def test_should_return_empty_list_when_no_array_found(self):
        result = extract_json_list("No array here.")
        assert result == []

    def test_should_return_empty_list_for_empty_string(self):
        assert extract_json_list("") == []

    def test_should_return_empty_list_for_invalid_json(self):
        result = extract_json_list("[broken]")
        assert result == []

    def test_should_extract_list_of_primitives(self):
        result = extract_json_list('```json\n["a", "b", "c"]\n```')
        assert result == ["a", "b", "c"]


class TestExtractJsonStrict:
    def test_should_return_dict_when_json_found(self):
        text = '{"result": "success"}'
        result = extract_json_strict(text)
        assert result == {"result": "success"}

    def test_should_raise_llm_response_error_when_no_json(self):
        with pytest.raises(LLMResponseError) as exc:
            extract_json_strict("No JSON here.")
        assert "No JSON object found" in str(exc.value)

    def test_should_raise_with_preview_of_response_in_error(self):
        text = "Plain text response from LLM."
        with pytest.raises(LLMResponseError) as exc:
            extract_json_strict(text)
        assert "Plain text response" in str(exc.value)

    def test_should_raise_for_empty_string(self):
        with pytest.raises(LLMResponseError):
            extract_json_strict("")
