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
from config import VERSION
from pathlib import Path

FILENAME_ADD_TIKZ = "tikz"
COLOR = "FF0088"


def get_next_file():
    current_dir = Path(".")

    # --- Search for matching files ---
    files = sorted(
        [
            file
            for file in current_dir.iterdir()
            if file.is_file()
            and file.suffix == ".tex"
            and not file.name.endswith("-pandoc.tex")
            and not file.name.endswith("-tikz.tex")
        ]
    )

    return str(files[0])


##############################################
############ MAIN FUNCTION ###################
##############################################


def convert_images():
    # if len(sys.argv) < 3:
    #     print("Za mało parametrów: python xxxxx.py <figures_folder> <filename>")
    #     sys.exit(1)

    figures_folder = f"{VERSION}-figures"
    filename = get_next_file()

    if figures_folder[-1] == "/":
        figures_folder = figures_folder[:-1]

    filename_noext = re.sub(r"\.[a-z]+$", "", filename)

    if not os.path.isfile(filename):
        print(f"Plik {filename} nie istnieje.")
        sys.exit(1)

    with open(filename, "r") as file:
        content = file.read()

    # usuniecie komentarzy
    print("- usuwam komentarze")
    content = remove_comments(content)

    # usuniecie zadan i rozwiazan
    print("- usuwam zadania i rozwiązania")
    content = re.sub(r"\\zadMat\{[0-9]+\}", "", content)
    content = re.sub(r"\\zadFiz\{[0-9]+\}", "", content)
    content = re.sub(r"\\rozMat(\[[0-9\-]+\])?\{[0-9]+\}", "", content)
    content = re.sub(r"\\rozFiz(\[[0-9\-]+\])?\{[0-9]+\}", "", content)
    content = re.sub(r"\\szrozFiz\{[0-9]+\}", "", content)

    # usuniecie input
    content = re.sub(r"\\input\s+[^\s]+\s", " ", content)
    content = re.sub(r"\\input\s+[^\\]+\\", "\\\\", content)

    # podstawienie '\def{\rysa} w miejsce pojawienia aby byla dobra kolejnosc
    matches = re.findall(
        r"(\\def(\\rys[^\{]*)\{(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})\})",
        content,
        flags=re.DOTALL,
    )
    matches2 = re.findall(
        r"(\\def(\\rys[^\{]*)\{(\\scalebox\{[^\}]*\}\{\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})\}\})",
        content,
        flags=re.DOTALL,
    )
    if len(matches + matches2) > 0:
        print("- podmieniam komendy \\def\\rysx")

    for match in sorted(matches + matches2, key=lambda x: -len(x[1])):
        content = content.replace(match[0], "")
        content = content.replace(match[1], match[2])

    content = re.sub(r"\\allowbreak", "", content, flags=re.DOTALL)

    # zamiana \ref na \eqref i usunięcie okalających nawiasów
    content = re.sub(
        r"\(\\ref\{([a-zA-Z0-9_]+)\}\)", r"\\eqref{\1}", content, flags=re.DOTALL
    )

    # zamiana \leqno(1) na \tag{1}
    content = re.sub(r"\\leqno\(([^)]+)\)", r"\\tag{\1}", content, flags=re.DOTALL)

    # specjalne formuly dla pliku z zadaniami
    if re.findall(r"\\zadanieM", content):
        newcommands = "\\theoremstyle{definition}\\newtheorem{exercise}{Zadanie}\n\\newtheorem{answer}{Rozwiązanie}\n\n"
        newcommands = (
            newcommands
            + "\\renewcommand{\\zadanieM}[3]{\\begin{exercise}{M #1.}#2\\begin{answer}#3\\end{answer}\\end{exercise}}\n"
        )
        newcommands = (
            newcommands
            + "\\renewcommand{\\zadanieF}[3]{\\begin{exercise}{F #1.}#2\\begin{answer}#3\\end{answer}\\end{exercise}}\n"
        )
        content = content.replace(
            "\\begin{document}", newcommands + "\n\\begin{document}\\title{Zadania}"
        )

    content = re.sub(r"\\angle", r"\\measuredangle", content)

    # ustawienie koloru
    content = content.replace(
        "\\begin{document}",
        "\\definecolor{deltaColor}{HTML}{"
        + COLOR
        + "}\n\\colorlet{magenta}{deltaColor}\n\n\\begin{document}",
    )

    # dodanie \usetkzobjc{all}, bo czesto sie nie kompiluje bez oraz ustawienie eksportowania obrazkow
    if len(re.findall(r"\\begin\{tikzpicture\}", content)) > 0:
        print("- TikZ: ustawiam eksportowanie obrazkow do katalogu " + figures_folder)
        # content = re.sub(r'\\usepackage\{tkz-euclide\}', '\\\\usepackage{tkz-euclide}\n\\\\usetkzobj{all}',content)
        content = re.sub(
            r"\\usepackage\{tikz\}",
            "\\\\usepackage{tikz}\n\\\\usetikzlibrary{external}\n\\\\tikzexternalize[shell escape=-enable-write18, prefix="
            + figures_folder
            + "/]\n\\\\tikzset{external/force remake}\n\\\\tikzset{/pgf/images/external info}\n\\\\tikzexternalize",
            content,
        )

    # TU SIĘ ZAPISUJE TIKZ
    filename_tikz = filename_noext + "-" + FILENAME_ADD_TIKZ + ".tex"
    with open(filename_tikz, "w") as file:
        file.write(content)

    if len(re.findall(r"\\begin\{tikzpicture\}", content)) > 0:
        # wywolanie pdflatex
        pdflatex_call_string = (
            'pdflatex --shell-escape -interaction=nonstopmode -file-line-error "'
            + filename_tikz
            + '"'
        )
        print("- TikZ: " + pdflatex_call_string)
        result = subprocess.run(
            pdflatex_call_string, shell=True, check=False, capture_output=True
        )
        if result.returncode != 0:
            print("! TikZ: error: pdflatex zwrócił błąd")
            print(result)
        else:
            print("- TikZ: sukces!")
            print(result)


##############################################
############ OTHER FUNCTIONS #################
##############################################


# usuwa zawartosc komentarzy oraz linie, w ktorych sa tylko komentarze
def remove_comments(content):
    content = re.sub(r"(?<=[^\\])%.*", "%", content)
    content = re.sub(r"\n([ \t]*%\n)*", "\n", content)
    content = re.sub(r"(?<=\~)\%\n", "", content, flags=re.DOTALL)

    return content


if __name__ == "__main__":
    print()
    print("### convert_images")
    convert_images()
    print("### convert_images done")
    print()