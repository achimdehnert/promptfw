"""Tests for promptfw.frontmatter module."""
import pytest
from pathlib import Path

from promptfw.frontmatter import render_frontmatter_file, render_frontmatter_string


class TestRenderFrontmatterString:
    """Tests for render_frontmatter_string()."""

    def test_basic_system_user(self):
        content = """---
system: "Du bist ein {{ role }}."
user: "Analysiere: {{ text }}"
---"""
        messages = render_frontmatter_string(content, role="Experte", text="Lorem")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Du bist ein Experte."
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Analysiere: Lorem"

    def test_system_only(self):
        content = """---
system: "Nur System-Prompt."
---"""
        messages = render_frontmatter_string(content)
        assert len(messages) == 1
        assert messages[0]["role"] == "system"

    def test_multiline_template(self):
        content = """---
system: |
  Du bist ein {{ role }}.
  Antworte auf {{ language }}.
user: |
  Frage: {{ question }}
---"""
        messages = render_frontmatter_string(
            content, role="Bot", language="Deutsch", question="Warum?"
        )
        assert "Bot" in messages[0]["content"]
        assert "Deutsch" in messages[0]["content"]
        assert "Warum?" in messages[1]["content"]

    def test_assistant_role(self):
        content = """---
system: "System."
assistant: "Beispiel-Antwort."
user: "Frage."
---"""
        messages = render_frontmatter_string(content)
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"

    def test_no_frontmatter_raises(self):
        with pytest.raises(ValueError, match="must start with YAML frontmatter"):
            render_frontmatter_string("No frontmatter here.")

    def test_invalid_frontmatter_raises(self):
        with pytest.raises(ValueError, match="expected --- ... --- format"):
            render_frontmatter_string("---\njust_a_string\n")

    def test_non_dict_frontmatter_raises(self):
        with pytest.raises(ValueError, match="must be a YAML dict"):
            render_frontmatter_string("---\n- list_item\n---\n")

    def test_empty_rendered_content_skipped(self):
        content = """---
system: "  "
user: "Hallo {{ name }}."
---"""
        messages = render_frontmatter_string(content, name="Welt")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_jinja2_conditionals(self):
        content = """---
system: "Du bist ein Reviewer."
user: |
  {% if chapter_text %}Kapitel: {{ chapter_text }}{% endif %}
  {% if focus %}Fokus: {{ focus }}{% endif %}
---"""
        messages = render_frontmatter_string(
            content, chapter_text="Einleitung", focus="Methodik"
        )
        assert "Einleitung" in messages[1]["content"]
        assert "Methodik" in messages[1]["content"]

    def test_jinja2_loop(self):
        content = """---
user: |
  Kapitel:
  {% for c in chapters %}- {{ c }}
  {% endfor %}
---"""
        messages = render_frontmatter_string(
            content, chapters=["Einleitung", "Methodik", "Ergebnisse"]
        )
        assert "Methodik" in messages[0]["content"]


class TestRenderFrontmatterFile:
    """Tests for render_frontmatter_file()."""

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            render_frontmatter_file("/nonexistent/template.jinja2")

    def test_load_from_file(self, tmp_path):
        tpl = tmp_path / "test.jinja2"
        tpl.write_text('---\nsystem: "Hallo {{ name }}."\n---\n')
        messages = render_frontmatter_file(tpl, name="Welt")
        assert messages[0]["content"] == "Hallo Welt."

    def test_load_accepts_string_path(self, tmp_path):
        tpl = tmp_path / "test.jinja2"
        tpl.write_text('---\nuser: "Test."\n---\n')
        messages = render_frontmatter_file(str(tpl))
        assert messages[0]["content"] == "Test."
