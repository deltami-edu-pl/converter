import re
from config import PATH

"""
For each delta-<folder>-*.html file (excluding *-pandoc.html and *-article.html),
extract the section between special HTML comments and write it to a new -article.html file,
replacing references to <folder>-figures with /media/<folder>-figures.
"""


def extract_article(content: str) -> str:
    start = "<!-- //// START OF ARTICLE //// -->"
    end = "<!-- //// END OF ARTICLE //// -->"

    pattern = re.compile(re.escape(start) + r"(.*?)" + re.escape(end), re.DOTALL)
    match = pattern.search(content)

    if match:
        extracted = match.group(0)
        figures_path = str(PATH.FIGURES)
        updated = extracted.replace(figures_path, f"/media/{figures_path}")
        return updated
    else:
        print(f"ERROR: No article block found in {content}")
        return content
