import json
import os
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParagraphNode:
    text: str
    is_list_item: bool
    list_id: Optional[str]
    nesting_level: int


@dataclass
class TableCellNode:
    nodes: list[ParagraphNode]
    col_span: int = 1
    row_span: int = 1


@dataclass
class TableRowNode:
    cells: list[TableCellNode]


@dataclass
class TableNode:
    rows: list[TableRowNode]


def apply_inline_text_styles(content, text_style):
    content = content.strip("\n")

    if text_style.get("link", {}).get("url"):
        content = f'<a href="{text_style["link"]["url"]}">{content}</a>'

    if text_style.get("baselineOffset"):
        match text_style["baselineOffset"]:
            case "SUPERSCRIPT":
                content = f"<sup>{content}</sup>"
            case "SUBSCRIPT":
                content = f"<sub>{content}</sub>"

    if text_style.get("backgroundColor"):
        rgb_color = text_style["backgroundColor"]["color"]["rgbColor"]
        content = (
            f'<mark style="background-color: rgb('
            f'{int(rgb_color.get("red", 0) * 100)}% '
            f'{int(rgb_color.get("green", 0) * 100)}% '
            f'{int(rgb_color.get("blue", 0) * 100)}%)">'
            f"{content}</mark>"
        )

    if text_style.get("underline"):
        content = f"<ins>{content}</ins>"
    if text_style.get("bold"):
        content = f"<b>{content}</b>"
    if text_style.get("italic"):
        content = f"<i>{content}</i>"
    if text_style.get("strikethrough"):
        content = f"<s>{content}</s>"

    return content


def parse_paragraph(paragraph) -> ParagraphNode:
    headings = {
        "HEADING_1": "# ",
        "HEADING_2": "## ",
        "HEADING_3": "### ",
        "HEADING_4": "#### ",
        "HEADING_5": "##### ",
        "HEADING_6": "###### ",
    }
    paragraph_style = paragraph["paragraphStyle"]
    is_heading = paragraph_style["namedStyleType"] in headings

    text = ""
    for item in paragraph["elements"]:
        text_run = item.get("textRun")
        if text_run:
            content = text_run["content"]
            text_style = text_run["textStyle"]
            if not is_heading:
                content = apply_inline_text_styles(content, text_style)
            text += content

    # no point in having empty tags, will make the doc messier
    if not text.strip():
        return ParagraphNode(
            text="",
            is_list_item=False,
            list_id=None,
            nesting_level=0,
        )

    # check if the paragraph has a heading, and remove the number labelling if it exists
    if is_heading:
        text = headings[paragraph_style["namedStyleType"]] + re.sub(
            r"^\d+(\.\d+)*\.*\s+", "", text
        )
    else:
        match paragraph_style.get("alignment"):
            case "CENTER":
                text = f'<p align="center">{text.strip("\n")}</p>'
            case "END":
                text = f'<p align="right">{text.strip("\n")}</p>'
            case "JUSTIFIED":
                text = f'<p align="justify">{text.strip("\n")}</p>'
            case "START":
                text = f'<p align="left">{text.strip("\n")}</p>'
            case _:
                text = f'<p>{text.strip("\n")}</p>'

    bullet_info = paragraph.get("bullet")
    is_list_item = bullet_info is not None
    return ParagraphNode(
        text=text,
        is_list_item=is_list_item,
        list_id=bullet_info["listId"] if is_list_item else None,
        nesting_level=bullet_info.get("nestingLevel", 0) if is_list_item else 0,
    )


def glyph_type_to_css(glyph_type: str) -> str:
    match glyph_type:
        case "ALPHA":
            return "lower-alpha"
        case "UPPER_ALPHA":
            return "upper-alpha"
        case "ROMAN":
            return "lower-roman"
        case "UPPER_ROMAN":
            return "upper-roman"
        case _:
            return "decimal"


def open_list_tag(list_type: str, style_type: str = "") -> str:
    """
    Open a <ul> or <ol> tag.
    If style_type is given (e.g. 'upper-alpha'), add a style attribute.
    """
    if style_type:
        return f'<{list_type} style="list-style-type: {style_type};">'
    else:
        return f"<{list_type}>"


def close_list_tag(list_type):
    return f"</{list_type}>"


def open_list_item():
    return "<li>"


def close_list_item():
    return "</li>"


def generate_table_html(table_data: TableNode, lists) -> str:
    output = []
    output.append("<table>")
    for idx, row in enumerate(table_data.rows):
        output.append("<tr>")
        for cell in row.cells:
            cell_html = generate_html(cell.nodes, lists)

            attrs = []
            if cell.row_span > 1:
                attrs.append(f'rowspan="{cell.row_span}"')
            if cell.col_span > 1:
                attrs.append(f'colspan="{cell.col_span}"')
            attr_str = " " + " ".join(attrs) if attrs else ""

            output.append(f"<th{attr_str}>" if idx == 0 else f"<td{attr_str}>")
            output.append(cell_html)
            output.append("</th>" if idx == 0 else "</td>")
        output.append("</tr>")
    output.append("</table>")
    return "\n".join(output)


def generate_list_html(node, lists, list_stack) -> str:
    output = []
    list_props = lists[node.list_id]["listProperties"]
    level_props = list_props["nestingLevels"][node.nesting_level]
    list_type = "ol" if "glyphType" in level_props else "ul"
    style_type = (
        glyph_type_to_css(level_props["glyphType"])
        if "glyphType" in level_props
        else ""
    )

    if len(list_stack) < node.nesting_level + 1:
        # open new levels
        while len(list_stack) < node.nesting_level + 1:
            list_stack.append({"type": list_type, "level": len(list_stack)})
            output.append(open_list_tag(list_type, style_type))

    # If we need to go shallower
    elif len(list_stack) > node.nesting_level + 1:
        while len(list_stack) > node.nesting_level + 1:
            top = list_stack.pop()
            output.append(close_list_tag(top["type"]))

    # If we remain at the same nesting level but changed from ul -> ol or vice versa
    if list_stack:
        top_list = list_stack[-1]
        if top_list["type"] != list_type:
            # close old
            old = list_stack.pop()
            output.append(close_list_tag(old["type"]))
            # open new
            list_stack.append({"type": list_type, "level": node.nesting_level})
            output.append(open_list_tag(list_type, style_type))
    else:
        # If stack is empty, open the list
        list_stack.append({"type": list_type, "level": node.nesting_level})
        output.append(open_list_tag(list_type, style_type))

    output.append(open_list_item())
    output.append(node.text.strip())
    output.append(close_list_item())
    return "\n".join(output)


def generate_html(nodes, lists) -> str:
    output = []
    list_stack = []

    for node in nodes:
        if isinstance(node, TableNode):
            # close out any lists
            while list_stack:
                top = list_stack.pop()
                output.append(close_list_tag(top["type"]))
            output.append(generate_table_html(node, lists))
            continue

        # the node is a paragraph node
        if node.is_list_item:
            output.append(generate_list_html(node, lists, list_stack))
        else:
            # Not a list item => close all open lists
            while list_stack:
                top = list_stack.pop()
                output.append(close_list_tag(top["type"]))
            output.append(node.text)

    # make sure that any lists that are still open are closed
    while list_stack:
        top = list_stack.pop()
        output.append(close_list_tag(top["type"]))

    return "\n".join(output)


def parse_table_cell(table_cell) -> TableCellNode:
    nodes = parse_content(table_cell)
    cell_style = table_cell.get("tableCellStyle", {})
    return TableCellNode(
        nodes=nodes,
        row_span=cell_style.get("rowSpan", 1),
        col_span=cell_style.get("colSpan", 1),
    )


def parse_table(table_elem) -> TableNode:
    # TODO: handle the blockquote thing
    rows = []
    for table_row in table_elem["tableRows"]:
        cells = []
        for table_cell in table_row["tableCells"]:
            cell_node = parse_table_cell(table_cell)
            if cell_node.nodes:
                cells.append(cell_node)
        rows.append(TableRowNode(cells=cells))
    return TableNode(rows=rows)


def parse_content(body):
    nodes = []
    for value in body["content"]:
        if "paragraph" in value:
            paragraph_node = parse_paragraph(value["paragraph"])
            if paragraph_node.text.strip():
                nodes.append(paragraph_node)
        if "table" in value:
            nodes.append(parse_table(value["table"]))
    return nodes


def parse_doc_body(data) -> str:
    return generate_html(parse_content(data["body"]), data["lists"])


def main():
    directory = "inputs/"
    # file = "headings_and_paragraphs_tables.json"
    file = "12b_notes_no_questions.json"

    json_file_path = os.path.join(directory, file)
    # print("Running Parser")
    # print(json_file_path)

    with open(json_file_path, "r") as file:
        data = json.load(file)
        print(parse_doc_body(data))


if __name__ == "__main__":
    main()
