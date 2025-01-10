import json
import os
import re


def apply_inline_text_styles(content, text_style):
    # it is important to make sure any HTML styles are applied first
    # before the native markdown, otherwise the rendering will not work properly
    if text_style.get("baselineOffset"):
        match text_style["baselineOffset"]:
            case "SUPERSCRIPT":
                content = f"<sup>{content.strip('\n')}</sup>"
            case "SUBSCRIPT":
                content = f"<sub>{content.strip('\n')}</sub>"

    # TODO: handle RGB colour styles
    if text_style.get("backgroundColor"):
        content = f"<mark>{content.strip('\n')}</mark>"
    if text_style.get("underline"):
        content = f"<ins>{content.strip('\n')}</ins>"

    if text_style.get("bold"):
        content = f"**{content.strip('\n')}**"
    if text_style.get("italic"):
        content = f"*{content.strip('\n')}*"
    if text_style.get("strikethrough"):
        content = f"~~{content.strip('\n')}~~"

    # TODO: links
    return content


def parse_paragraph(element):
    headings = {
        "HEADING_1": "# ",
        "HEADING_2": "## ",
        "HEADING_3": "### ",
        "HEADING_4": "#### ",
        "HEADING_5": "##### ",
        "HEADING_6": "###### ",
    }
    text = ""
    elements = element["paragraph"]["elements"]
    paragraph_style = element["paragraph"]["paragraphStyle"]
    is_heading = paragraph_style["namedStyleType"] in headings

    for element in elements:
        text_run = element.get("textRun")
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
    return text


def read_doc_content(content):
    text = ""
    for value in content:
        if "paragraph" in value:
            text += "\n" + parse_paragraph(value)

    return text


def main():
    directory = "inputs/"
    file = "headings_and_paragraphs_advanced.json"

    json_file_path = os.path.join(directory, file)
    print("Running Parser")
    print(json_file_path)

    with open(json_file_path, "r") as file:
        data = json.load(file)
        print(f"Parsing Note: {data['title']}")
        content = data["body"]["content"]
        print(read_doc_content(content))


if __name__ == "__main__":
    main()
