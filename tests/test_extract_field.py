"""Tests for extract_field() — issue #8."""

from promptfw.parsing import extract_field


class TestExtractField:
    def test_should_extract_bold_field(self):
        text = "**Premise:** Eine Geschichte über einen Schmied.\n**Themes:** Macht"
        assert extract_field(text, "Premise") == "Eine Geschichte über einen Schmied."

    def test_should_extract_second_field(self):
        text = "**Premise:** Eine Geschichte.\n**Themes:** Identität, Macht"
        assert extract_field(text, "Themes") == "Identität, Macht"

    def test_should_be_case_insensitive(self):
        text = "**premise:** Wert"
        assert extract_field(text, "Premise") == "Wert"
        assert extract_field(text, "PREMISE") == "Wert"

    def test_should_extract_plain_colon_field(self):
        text = "Premise: Eine Geschichte.\nThemes: Macht"
        assert extract_field(text, "Premise") == "Eine Geschichte."

    def test_should_return_none_for_missing_field(self):
        text = "**Premise:** Wert"
        assert extract_field(text, "Missing") is None

    def test_should_return_default_for_missing_field(self):
        text = "**Premise:** Wert"
        assert extract_field(text, "Missing", default="") == ""

    def test_should_return_default_for_empty_text(self):
        assert extract_field("", "Premise", default="x") == "x"

    def test_should_return_default_for_whitespace_only(self):
        assert extract_field("   \n", "Premise") is None

    def test_should_extract_multiline_value(self):
        text = "**Summary:** Erste Zeile.\nZweite Zeile.\n**Title:** Foo"
        result = extract_field(text, "Summary")
        assert "Erste Zeile." in result
        assert "Zweite Zeile." in result

    def test_should_handle_three_fields(self):
        text = (
            "**Title:** Der Schmied\n"
            "**Premise:** Ein Mann entdeckt Magie.\n"
            "**Themes:** Identität, Macht, Verantwortung"
        )
        assert extract_field(text, "Title") == "Der Schmied"
        assert extract_field(text, "Premise") == "Ein Mann entdeckt Magie."
        assert extract_field(text, "Themes") == "Identität, Macht, Verantwortung"
