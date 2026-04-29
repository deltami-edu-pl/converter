#!/usr/bin/env python3

import re
import subprocess
from pathlib import Path
from config import PATH, FILE, COLOR
from helper import log_section, convert_pdf_to_png, contain_tikz


@log_section
def convert_images():

    content = FILE().source.tex.read_text(encoding="utf-8")

    # # usuniecie komentarzy
    # # print("- usuwam komentarze")
    # content = re.sub(r"(?<=[^\\])%.*", "%", content)
    # content = re.sub(r"\n([ \t]*%\n)*", "\n", content)
    # content = re.sub(r"(?<=\~)\%\n", "", content, flags=re.DOTALL)

    # # usuniecie zadan i rozwiazan
    # # print("- usuwam zadania i rozwiązania")
    # content = re.sub(r"\\zadMat\{[0-9]+\}", "", content)
    # content = re.sub(r"\\zadFiz\{[0-9]+\}", "", content)
    # content = re.sub(r"\\rozMat(\[[0-9\-]+\])?\{[0-9]+\}", "", content)
    # content = re.sub(r"\\rozFiz(\[[0-9\-]+\])?\{[0-9]+\}", "", content)
    # content = re.sub(r"\\szrozFiz\{[0-9]+\}", "", content)

    # # usuniecie input
    # content = re.sub(r"\\input\s+[^\s]+\s", " ", content)
    # content = re.sub(r"\\input\s+[^\\]+\\", "\\\\", content)

    content = re.sub(r"\\angle", r"\\measuredangle", content)

    # ustawienie koloru
    # + safety net na polskie operatory trygonometryczne ktorych delta.sty nie definiuje,
    #   a uzywane sa w tikzpicture (np. \tg w 02-miskiewicz). \providecommand nie nadpisze
    #   istniejacej definicji, wiec to bezpieczne.
    content = content.replace(
        "\\begin{document}",
        "\\definecolor{deltaColor}{HTML}{"
        + COLOR
        + "}\n\\colorlet{magenta}{deltaColor}\n\n"
        "\\providecommand{\\tg}{\\operatorname{tg}}\n"
        "\\providecommand{\\ctg}{\\operatorname{ctg}}\n"
        "\\providecommand{\\arctg}{\\operatorname{arc\\,tg}}\n"
        "\\providecommand{\\arcctg}{\\operatorname{arc\\,ctg}}\n\n"
        "\\begin{document}",
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

    # wyodrębnienie wszystkich tikzpicture i zastąpienie zawartości dokumentu tylko nimi
    tikzpictures = re.findall(
        r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
        content,
        flags=re.DOTALL,
    )
    # również tikzpicture w scalebox
    tikzpictures_scalebox = re.findall(
        r"\\scalebox\{[^\}]*\}\{\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}\}",
        content,
        flags=re.DOTALL,
    )
    all_tikzpictures = tikzpictures + tikzpictures_scalebox
    # ##1 -> #1: tikzpictures sa wyciagane z wnetrza \def\rysX{...}, wiec zdejmujemy
    # jeden poziom zagniezdzenia gdy ekstraktujemy je do standalone'owego dokumentu
    all_tikzpictures = [re.sub(r"##(\d)", r"#\1", tp) for tp in all_tikzpictures]

    print(f"# Found {len(all_tikzpictures)} tikzpicture blocks")
    # znajdź \begin{document} i \end{document}
    doc_start = content.find("\\begin{document}")
    doc_end = content.find("\\end{document}")

    if doc_start != -1 and doc_end != -1:
        # przed \begin{document}
        before_doc = content[: doc_start + len("\\begin{document}")]
        # po \end{document}
        after_doc = content[doc_end:]
        # zawartość dokumentu to tylko tikzpicture
        doc_content = "\n\n" + "\n\n".join(all_tikzpictures) + "\n\n"
        # złożenie z powrotem
        content = before_doc + doc_content + after_doc

    # TU SIĘ ZAPISUJE TIKZ
    image_tex = FILE().images.tex
    image_tex.write_text(content, encoding="utf-8")

    if contain_tikz(content):
        print(str(image_tex))
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
            print(result)
        # else:
        # print("- TikZ: sukces!")
        # print(result)

        convert_externalized_pdfs_for_tex(image_tex)


def convert_externalized_pdfs_for_tex(image_tex: Path):
    job_prefix = image_tex.stem + "-figure"  # "01-byczuk-tikz"

    # 1) znajdź PDF-y pasujące do job_prefix
    # TikZ externalize zwykle robi nazwy typu:
    # <job_prefix>-figure0.pdf, <job_prefix>-figure1.pdf ... albo podobnie
    pdf_files = sorted(PATH.ROOT.glob(f"{job_prefix}*.pdf"))
    print(
        f"# Found {len(pdf_files)} PDF files for prefix '{job_prefix}' in {PATH.ROOT}"
    )

    if not pdf_files:
        print(f"WARNING: No PDFs found for prefix '{job_prefix}' in {PATH.ROOT}")
        return

    converted_files_error = 0
    converted_files_count = 0

    # 2) konwersja + sprzątanie
    for pdf_file in pdf_files:
        # --- KONWERSJA PDF -> PNG (Twój kod) ---
        dest_path = PATH.FIGURES / (
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
    junk_exts = {
        ".md5",
        ".dpth",
        ".log",
        ".aux",
        ".synctex.gz",
        ".pdf",
        ".auxlock",
        ".out",
    }
    for ext in junk_exts:
        junk_path = pdf_file.with_name(stem + ext)
        if junk_path.exists():
            try:
                junk_path.unlink()
            except Exception as e:
                print(f"WARNING: Can't remove {junk_path}: {e}")


if __name__ == "__main__":
    convert_images()
