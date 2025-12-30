from config import PATH


def wrap_with_main(content: str) -> str | None:
    content_main = PATH.DELTA.read_text(encoding="utf-8")

    start_position = content_main.find("\\begin{document}")
    if start_position != -1:
        content_main = content_main[:start_position]

    end_position = content.find("\\endinput")
    if end_position != -1:
        content = content[:end_position]

    content = content_main + "\\begin{document}\n" + content + "\\end{document}"

    return content
