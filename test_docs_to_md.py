import pytest

from docs_to_md import ParagraphData, apply_inline_text_styles, parse_paragraph


@pytest.fixture
def text_str():
    return "Hello world"


class TestApplyInlineTextStyles:
    @pytest.mark.parametrize(
        "text_styles,expected",
        [
            ({"bold": True}, "<b>Hello world</b>"),
            ({"italic": True}, "<i>Hello world</i>"),
            ({"underline": True}, "<ins>Hello world</ins>"),
            ({"strikethrough": True}, "<s>Hello world</s>"),
            ({"bold": True, "italic": True}, "<i><b>Hello world</b></i>"),
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

    @pytest.mark.parametrize(
        "text_styles,expected",
        [
            (
                {"backgroundColor": {"color": {"rgbColor": {"red": 1, "green": 1}}}},
                '<mark style="background-color: rgb(100% 100% 0%)">Hello world</mark>',
            ),
            (
                {
                    "backgroundColor": {
                        "color": {
                            "rgbColor": {
                                "red": 0.6431373,
                                "green": 0.7607843,
                                "blue": 0.95686275,
                            }
                        }
                    }
                },
                '<mark style="background-color: rgb(64% 76% 95%)">Hello world</mark>',
            ),
            (
                {
                    "bold": True,
                    "backgroundColor": {"color": {"rgbColor": {"red": 1, "green": 1}}},
                },
                '<b><mark style="background-color: rgb(100% 100% 0%)">Hello world</mark></b>',
            ),
        ],
    )
    def test_text_highlighting(self, text_str, text_styles, expected):
        assert apply_inline_text_styles(text_str, text_styles) == expected

    @pytest.mark.parametrize(
        "text_styles,expected",
        [
            (
                {"link": {"url": "https://hello-world.com"}},
                '<a href="https://hello-world.com">Hello world</a>',
            ),
            (
                {"underline": True, "link": {"url": "https://hello-world.com"}},
                '<ins><a href="https://hello-world.com">Hello world</a></ins>',
            ),
            (
                {"bold": True, "link": {"url": "https://hello-world.com"}},
                '<b><a href="https://hello-world.com">Hello world</a></b>',
            ),
        ],
    )
    def test_text_links(self, text_str, text_styles, expected):
        assert apply_inline_text_styles(text_str, text_styles) == expected


"""
TESTS:
- test parse_paragraph
    - empty text case
    - test headings/removing labelling if it exists
    - test paragraph alignment
    - test if is bullet
    - test if nested bullet
- read_doc_content (this will probably be an integration test)
    - test basic multiple paragraphs
    - test bullet points ul
    - test ul nesting
    - test ol
    - test ol nesting
"""


class TestParseParagraph:
    @pytest.fixture
    def paragraph_element(self):
        return {
            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
            "elements": [
                {"textRun": {"content": "Hello ", "textStyle": {}}},
                {"textRun": {"content": "World.", "textStyle": {}}},
            ],
        }

    def test_parse_basic_paragraph(self, paragraph_element):
        assert parse_paragraph(paragraph_element) == ParagraphData(
            text="<p>Hello World.</p>",
            is_list_item=False,
            list_id=None,
            nesting_level=0,
        )

    @pytest.mark.parametrize(
        "elem",
        [
            {
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "elements": [
                    {"textRun": {"content": "\n", "textStyle": {}}},
                ],
            },
            {
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "elements": [
                    {"textRun": {"content": "", "textStyle": {}}},
                ],
            },
            {
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "elements": [
                    {"textRun": {"content": "   ", "textStyle": {}}},
                ],
            },
            {
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "elements": [
                    {"textRun": {"content": "\t", "textStyle": {}}},
                ],
            },
        ],
    )
    def test_parse_whitespace_only_text(self, elem):
        assert parse_paragraph(elem) == ParagraphData(
            text="", is_list_item=False, list_id=None, nesting_level=0
        )

    def test_parse_headings(self):
        elem = {
            "paragraphStyle": {"namedStyleType": "HEADING_1"},
            "elements": [
                {"textRun": {"content": "1.1 Hello World.", "textStyle": {}}},
            ],
        }

        assert parse_paragraph(elem) == ParagraphData(
            text="# Hello World.",
            is_list_item=False,
            list_id=None,
            nesting_level=0,
        )

    def test_parse_headings_no_numbers(self):
        elem = {
            "paragraphStyle": {"namedStyleType": "HEADING_1"},
            "elements": [
                {"textRun": {"content": "Hello World.", "textStyle": {}}},
            ],
        }

        assert parse_paragraph(elem) == ParagraphData(
            text="# Hello World.",
            is_list_item=False,
            list_id=None,
            nesting_level=0,
        )

    def test_parse_text_align(self):
        elem = {
            "paragraphStyle": {
                "namedStyleType": "NORMAL_TEXT",
                "alignment": "JUSTIFIED",
            },
            "elements": [
                {"textRun": {"content": "Hello ", "textStyle": {}}},
                {"textRun": {"content": "World.", "textStyle": {}}},
            ],
        }

        assert parse_paragraph(elem) == ParagraphData(
            text='<p align="justify">Hello World.</p>',
            is_list_item=False,
            list_id=None,
            nesting_level=0,
        )

    def test_parse_bullet(self):
        elem = {
            "paragraphStyle": {
                "namedStyleType": "NORMAL_TEXT",
            },
            "elements": [
                {"textRun": {"content": "Hello ", "textStyle": {}}},
                {"textRun": {"content": "World.", "textStyle": {}}},
            ],
            "bullet": {"listId": "1", "nestingLevel": 0},
        }

        assert parse_paragraph(elem) == ParagraphData(
            text="<p>Hello World.</p>",
            is_list_item=True,
            list_id="1",
            nesting_level=0,
        )

    def test_parse_bullet_nested(self):
        elem = {
            "paragraphStyle": {
                "namedStyleType": "NORMAL_TEXT",
            },
            "elements": [
                {"textRun": {"content": "Hello ", "textStyle": {}}},
                {"textRun": {"content": "World.", "textStyle": {}}},
            ],
            "bullet": {"listId": "1", "nestingLevel": 1},
        }

        assert parse_paragraph(elem) == ParagraphData(
            text="<p>Hello World.</p>",
            is_list_item=True,
            list_id="1",
            nesting_level=1,
        )
