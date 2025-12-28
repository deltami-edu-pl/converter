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
    PATH_ROOT,
    PATH_FIGURES,
    convert_pdf_to_png,
    contain_tikz,
)
from pathlib import Path
from wand.image import Image


@log_section
def convert_images():

    content = GET_NEXT().read_text(encoding="utf-8")

    # usuniecie komentarzy
    # print("- usuwam komentarze")
    content = re.sub(r"(?<=[^\\])%.*", "%", content)
    content = re.sub(r"\n([ \t]*%\n)*", "\n", content)
    content = re.sub(r"(?<=\~)\%\n", "", content, flags=re.DOTALL)

    # usuniecie zadan i rozwiazan
    # print("- usuwam zadania i rozwiązania")
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
    # if len(re.findall(r"\\begin\{tikzpicture\}", content)) > 0:
    # print("- TikZ: ustawiam eksportowanie obrazkow do katalogu " + figures_folder)
    # content = re.sub(r'\\usepackage\{tkz-euclide\}', '\\\\usepackage{tkz-euclide}\n\\\\usetkzobj{all}',content)

    tikz_block = rf"""
    \\usepackage{{tikz}}
    \\usetikzlibrary{{external}}
    \\tikzexternalize[
        shell escape=-enable-write18,
        prefix=./
    ]
    \\tikzset{{external/force remake}}
    \\tikzset{{/pgf/images/external info}}
    \\tikzexternalize
    """.strip()

    content = re.sub(
        r"\\usepackage\{tikz\}",
        tikz_block,
        content,
    )

    # content = re.sub(
    #     r"\\usepackage\{tikz\}",
    #     "\\\\usepackage{tikz}\n\\\\usetikzlibrary{external}\n\\\\tikzexternalize[shell escape=-enable-write18, prefix="
    #     + figures_folder
    #     + "/]\n\\\\tikzset{external/force remake}\n\\\\tikzset{/pgf/images/external info}\n\\\\tikzexternalize",
    #     content,
    # )

    # TU SIĘ ZAPISUJE TIKZ
    image_tex = PATH_ROOT / (GET_NEXT().stem + "-" + IMAGES + ".tex")
    image_tex.write_text(content, encoding="utf-8")

    if contain_tikz(content):
    # wywolanie pdflatex
        pdflatex_call_string = (
            'pdflatex --shell-escape -interaction=nonstopmode -file-line-error "'
            + str(image_tex)
            + '"'
        )
        # print("- TikZ: " + pdflatex_call_string)
        result = subprocess.run(
            pdflatex_call_string, shell=True, check=False, capture_output=True
        )
        if result.returncode != 0:
            print("# ERROR: pdflatex zwrócił błąd")
            # print(result)
        # else:
            # print("- TikZ: sukces!")
            # print(result)

        convert_externalized_pdfs_for_tex(image_tex)


def convert_externalized_pdfs_for_tex(image_tex: Path):
    job_prefix = image_tex.stem + "-figure"  # "01-byczuk-tikz"

    # 1) znajdź PDF-y pasujące do job_prefix
    # TikZ externalize zwykle robi nazwy typu:
    # <job_prefix>-figure0.pdf, <job_prefix>-figure1.pdf ... albo podobnie
    pdf_files = sorted(PATH_ROOT.glob(f"{job_prefix}*.pdf"))
    print(f"# Found {len(pdf_files)} PDF files for prefix '{job_prefix}' in {PATH_ROOT}")

    if not pdf_files:
        print(f"WARNING: No PDFs found for prefix '{job_prefix}' in {PATH_ROOT}")
        return

    converted_files_error = 0
    converted_files_count = 0

    # 2) konwersja + sprzątanie
    for pdf_file in pdf_files:
        # --- KONWERSJA PDF -> PNG (Twój kod) ---
        dest_path = PATH_FIGURES / (
            pdf_file.stem.replace("-eps-converted-to", "") + ".png"
        )
        if convert_pdf_to_png(pdf_file, dest_path):
            converted_files_count += 1
            remove_junk_files(pdf_file)
            print(f"# Converted {pdf_file.name} to {dest_path}")
        else:
            converted_files_error += 1

    print(f"# Converted {converted_files_count} files")
    remove_junk_files(image_tex)

    if converted_files_error > 0:
        print(f"# ERROR: {converted_files_error} files conversion failed")


def remove_junk_files(pdf_file: Path):
    stem = pdf_file.stem  # np. "01-byczuk-tikz-figure0"
    # rozszerzenia, które chcesz usuwać jako "cache/śmieci" dla tych samych stemów
    junk_exts = {".md5", ".dpth", ".log", ".aux", ".synctex.gz", ".pdf", ".auxlock", ".out"}
    for ext in junk_exts:
        junk_path = pdf_file.with_name(stem + ext)
        if junk_path.exists():
            try:
                junk_path.unlink()
            except Exception as e:
                print(f"WARNING: Can't remove {junk_path}: {e}")

if __name__ == "__main__":
    convert_images()
