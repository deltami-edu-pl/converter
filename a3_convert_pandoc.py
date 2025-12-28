#!/usr/bin/env python3

import unicodedata
import re
import os
import requests
import urllib.error
import sys
import urllib.parse
from bs4 import BeautifulSoup
from bs4 import Comment
from urllib.parse import urljoin, urlparse
from urllib.request import urlretrieve
import subprocess
from config import (
    VERSION,
    GET_NEXT,
    log_section,
    COLOR,
    IMAGES,
    PANDOC,
    PATH_FIGURES,
    PATH_ROOT,
    contain_tikz,
)
from a3a_prepare_pandoc import prepare_pandoc
from a3b_correct_html import correct_html
from a3c_extract_article import extract_article


@log_section
def convert_pandoc():
    content = prepare_pandoc()

    # TU SIĘ ZAPISUJE PANDOC
    pandoc_tex = PATH_ROOT / (GET_NEXT().stem + "-" + PANDOC + ".tex")
    pandoc_html = PATH_ROOT / (GET_NEXT().stem + "-" + PANDOC + ".html")
    final_html = PATH_ROOT / (GET_NEXT().stem + ".html")

    pandoc_tex.write_text(content, encoding="utf-8")

    pandoc_call_string = (
        "pandoc --wrap=preserve "
        + str(pandoc_tex)
        + " -t html -V lang=pl --mathjax -s -o "
        + str(pandoc_html)
    )
    print("- Pandoc: " + pandoc_call_string)
    result = subprocess.run(
        pandoc_call_string, shell=True, check=False, capture_output=True
    )
    if result.stderr:
        print("! Pandoc: error: pandoc zwrócił błąd")
        print(result.stderr)

    if not pandoc_html.exists():
        print(f"! Pandoc: plik " + pandoc_html.name + " nie istnieje")
        print(f"! END: niestety nie udalo sie stworzyc htmla")
        sys.exit(1)
    print(f"- Pandoc: sukces! aby sprawdzic ostrzezenia uruchom komende:")
    print(pandoc_call_string + " --verbose")

    html_content = pandoc_html.read_text(encoding="utf-8")

    newsoup = correct_html(html_content)

    final_html_content = re.sub(r"\n\n\n+", r"\n\n", str(newsoup))
    # final_html_content = newsoup.encode('utf-8')
    final_html.write_text(final_html_content, encoding="utf-8")

    print(f"- SUKCES! plik " + str(final_html) + " stworzony!")

    # USUWAM WSZYSTKIE PLIKI TYMCZASOWE
    # os.remove(filename_pandoc_after)
    extract_article()


if __name__ == "__main__":
    convert_pandoc()
