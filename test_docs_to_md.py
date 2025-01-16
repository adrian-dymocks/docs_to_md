import pytest

from docs_to_md import (
    ParagraphData,
    apply_inline_text_styles,
    build_html,
    parse_paragraph,
)


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


class TestBuildHTML:
    @pytest.fixture
    def lists(self):
        return {
            "1": {"listProperties": {"nestingLevels": [{}, {}, {}, {}]}},
            "2": {
                "listProperties": {
                    "nestingLevels": [
                        {"glyphType": "DECIMAL"},
                        {"glyphType": "ALPHA"},
                        {"glyphType": "ROMAN"},
                        {"glyphType": "DECIMAL"},
                    ]
                }
            },
        }

    def test_basic_nodes(self, lists):
        nodes = [
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=False,
                list_id=None,
                nesting_level=0,
            ),
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=False,
                list_id=None,
                nesting_level=0,
            ),
        ]
        assert (
            build_html(nodes, lists)
            == """<p>Hello World.</p>
<p>Hello World.</p>"""
        )

    def test_basic_unordered_lists(self, lists):
        nodes = [
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=True,
                list_id="1",
                nesting_level=0,
            ),
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=True,
                list_id="1",
                nesting_level=0,
            ),
        ]
        assert (
            build_html(nodes, lists)
            == """<ul>
<li>
<p>Hello World.</p>
</li>
<li>
<p>Hello World.</p>
</li>
</ul>"""
        )

    def test_nested_unordered_lists(self, lists):
        nodes = [
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=True,
                list_id="1",
                nesting_level=0,
            ),
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=True,
                list_id="1",
                nesting_level=1,
            ),
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=True,
                list_id="1",
                nesting_level=2,
            ),
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=True,
                list_id="1",
                nesting_level=0,
            ),
        ]
        assert (
            build_html(nodes, lists)
            == """<ul>
<li>
<p>Hello World.</p>
</li>
<ul>
<li>
<p>Hello World.</p>
</li>
<ul>
<li>
<p>Hello World.</p>
</li>
</ul>
</ul>
<li>
<p>Hello World.</p>
</li>
</ul>"""
        )

    def test_basic_ordered_lists(self, lists):
        nodes = [
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=True,
                list_id="2",
                nesting_level=0,
            ),
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=True,
                list_id="2",
                nesting_level=0,
            ),
        ]
        assert (
            build_html(nodes, lists)
            == """<ol style="list-style-type: decimal;">
<li>
<p>Hello World.</p>
</li>
<li>
<p>Hello World.</p>
</li>
</ol>"""
        )

    def test_nested_ordered_lists(self, lists):
        nodes = [
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=True,
                list_id="2",
                nesting_level=0,
            ),
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=True,
                list_id="2",
                nesting_level=1,
            ),
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=True,
                list_id="2",
                nesting_level=2,
            ),
            ParagraphData(
                text="<p>Hello World.</p>",
                is_list_item=True,
                list_id="2",
                nesting_level=0,
            ),
        ]
        assert (
            build_html(nodes, lists)
            == """<ol style="list-style-type: decimal;">
<li>
<p>Hello World.</p>
</li>
<ol style="list-style-type: lower-alpha;">
<li>
<p>Hello World.</p>
</li>
<ol style="list-style-type: lower-roman;">
<li>
<p>Hello World.</p>
</li>
</ol>
</ol>
<li>
<p>Hello World.</p>
</li>
</ol>"""
        )
