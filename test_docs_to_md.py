import pytest

from docs_to_md import apply_inline_text_styles


@pytest.fixture
def text_str():
    return "Hello world"


class TestApplyInlineTextStyles:
    @pytest.mark.parametrize(
        "text_styles,expected",
        [
            ({"bold": True}, "**Hello world**"),
            ({"italic": True}, "*Hello world*"),
            ({"underline": True}, "<ins>Hello world</ins>"),
            ({"strikethrough": True}, "~~Hello world~~"),
            ({"bold": True, "italic": True}, "***Hello world***"),
            ({}, "Hello world"),
            ({"bold": False}, "Hello world"),
            ({"italic": False}, "Hello world"),
            ({"underline": False}, "Hello world"),
            ({"strikethrough": False}, "Hello world"),
        ],
    )
    def test_applying_inline_styles(self, text_str, text_styles, expected):
        assert apply_inline_text_styles(text_str, text_styles) == expected

    @pytest.mark.parametrize(
        "text,text_styles,expected",
        [
            ("2", {"baselineOffset": "SUBSCRIPT"}, "<sub>2</sub>"),
            ("2", {"baselineOffset": "SUPERSCRIPT"}, "<sup>2</sup>"),
        ],
    )
    def test_superscript_and_subscript(self, text, text_styles, expected):
        assert apply_inline_text_styles(text, text_styles) == expected
