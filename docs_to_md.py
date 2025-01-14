import json
import math
import os
import re


def apply_inline_text_styles(content, text_style):
    if text_style.get("link", {}).get("url"):
        content = f"[{content.strip('\n')}]({text_style['link']['url']})"

    # it is important to make sure any HTML styles are applied first (links are fine)
    # before the native markdown, otherwise the rendering will not work properly
    if text_style.get("baselineOffset"):
        match text_style["baselineOffset"]:
            case "SUPERSCRIPT":
                content = f"<sup>{content.strip('\n')}</sup>"
            case "SUBSCRIPT":
                content = f"<sub>{content.strip('\n')}</sub>"

    if text_style.get("backgroundColor"):
        # each value is represented as a number from 0.0 to 1.0
        rgb_color = text_style["backgroundColor"]["color"]["rgbColor"]
        red = math.floor(rgb_color.get("red", 0) * 100)
        green = math.floor(rgb_color.get("green", 0) * 100)
        blue = math.floor(rgb_color.get("blue", 0) * 100)
        content = f"<mark style=\"background-color: rgb({red}% {green}% {blue}%)\">{content.strip('\n')}</mark>"

    if text_style.get("underline"):
        content = f"<ins>{content.strip('\n')}</ins>"

    if text_style.get("bold"):
        content = f"**{content.strip('\n')}**"
    if text_style.get("italic"):
        content = f"*{content.strip('\n')}*"
    if text_style.get("strikethrough"):
        content = f"~~{content.strip('\n')}~~"

    return content


def parse_paragraph(element, lists, list_stack):
    headings = {
        "HEADING_1": "# ",
        "HEADING_2": "## ",
        "HEADING_3": "### ",
        "HEADING_4": "#### ",
        "HEADING_5": "##### ",
        "HEADING_6": "###### ",
    }
    text = ""
    paragraph = element["paragraph"]
    elements = paragraph["elements"]
    paragraph_style = paragraph["paragraphStyle"]
    is_heading = paragraph_style["namedStyleType"] in headings

    for item in elements:
        text_run = item.get("textRun")
        if not text_run:
            continue

        content = text_run["content"]
        text_style = text_run["textStyle"]

        # we do not want to use inline styles for headings
        if not is_heading:
            content = apply_inline_text_styles(content, text_style)

        text += content

    # check if the paragraph has a heading, and remove the number labelling
    if is_heading:
        text = headings[paragraph_style["namedStyleType"]] + re.sub(
            r"^\d+(\.\d+)*\s+", "", text
        )

    # check if the paragraph is a list item
    bullet = paragraph.get("bullet")
    if bullet:
        list_id = bullet["listId"]
        list_properties = lists[list_id]["listProperties"]

        nesting_level = bullet.get("nestingLevel", 0)
        nesting_levels = list_properties["nestingLevels"]
        level_properties = nesting_levels[nesting_level]

        # glyphType is only present in ordered lists
        # TODO: deal with different ordered list types (alphabetical, roman)
        if "glyphType" in level_properties:
            desired_length = nesting_level + 1
            if desired_length > len(list_stack):
                # we need to go deeper
                while len(list_stack) < desired_length:
                    list_stack.append(1)
            elif desired_length < len(list_stack):
                # we need to go shallower
                while len(list_stack) > desired_length:
                    list_stack.pop()
                list_stack[-1] += 1
            else:
                # same level
                if not list_stack:
                    list_stack.append(1)
                else:
                    list_stack[-1] += 1
            text = "  " * nesting_level + f"{list_stack[-1]}. {text}"
        else:
            text = "  " * nesting_level + f"- {text}"

    else:
        list_stack.clear()
    return text


def read_doc_content(data):
    text = ""
    lists = data["lists"]
    body = data["body"]
    content = body["content"]
    list_stack = []
    for value in content:
        if "paragraph" in value:
            text += "\n" + parse_paragraph(value, lists, list_stack)

    return text


def main():
    directory = "inputs/"
    file = "headings_and_paragraphs_advanced2.json"

    json_file_path = os.path.join(directory, file)
    # print("Running Parser")
    # print(json_file_path)

    with open(json_file_path, "r") as file:
        data = json.load(file)
        print(read_doc_content(data))


if __name__ == "__main__":
    main()
