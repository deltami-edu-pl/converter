import re
from config import VERSION, PATH_ROOT, log_section

"""
For each delta-<folder>-*.html file (excluding *-pandoc.html and *-article.html),
extract the section between special HTML comments and write it to a new -article.html file,
replacing references to <folder>-figures with /media/<folder>-figures.
"""


@log_section
def extract_article():
    start = "<!-- //// START OF ARTICLE //// -->"
    end = "<!-- //// END OF ARTICLE //// -->"

    for file in PATH_ROOT.glob("*.html"):
        # Skip unwanted files
        if (
            file.name.endswith("-pandoc.html")
            or file.name.endswith("-article.html")
            or file.name.endswith("convert.html")
            or file.name.endswith("template.html")
        ):
            continue

        pattern = re.compile(re.escape(start) + r"(.*?)" + re.escape(end), re.DOTALL)
        content = file.read_text(encoding="utf-8")
        match = pattern.search(content)

        if match:
            extracted = match.group(0)
            updated = extracted.replace(
                f"{VERSION}-figures", f"/media/{VERSION}-figures"
            )
            new_file = file.with_name(file.stem + "-article.html")
            new_file.write_text(updated, encoding="utf-8")
            print(f"# Created {new_file.name}")
        else:
            print(f"ERROR: No article block found in {file.name}")


if __name__ == "__main__":
    extract_article()
