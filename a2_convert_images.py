#!/usr/bin/env python3

import re
import subprocess
from pathlib import Path
from config import PATH, FILE, COLOR
from helper import log_section, convert_pdf_to_png, contain_tikz, wrap_overlay_centerlines


def _extract_newcommands_as_provide(content: str) -> str:
    """
    Znajduje wszystkie \\newcommand{\\name}[args][default]{body} w content
    z prawidlowym balansem klamerek (regex nie ogarnia, bo body moze byc
    wieloliniowe z zagniezdzonymi {}). Dodatkowo wyciaga \\definecolor{...}
    i \\colorlet{...} - czesto sa definiowane w body przed tikzpicture
    (np. 03-rajkowski definiuje c1/c2/c3 inline) i bez nich pdflatex
    przewraca sie na nieznanym kolorze w tikzu.

    Zwraca tekst zlozony z tych definicji (newcommandy zamienione na
    providecommand, zeby nie kolidowac z delta.sty), oddzielonych
    nowymi liniami, zakonczony '\\n\\n' jezeli cokolwiek znaleziono -
    albo pusty string.

    UWAGA: definicje, ktorych body zawiera cale \\begin{tikzpicture}
    (np. `\\def\\rysa{\\begin{tikzpicture}...}` w 02-gornicki, 09-ligi),
    sa POMIJANE. Inaczej ten sam tikzpicture trafia do dokumentu dwa razy -
    raz z hoistowanej preambuly, raz z body - wiec pdflatex renderuje go
    podwojnie, a numeracja figureN w a2 rozjezdza sie z numeracja w
    a3a3_replace_images (ktore liczy tikzpicture tylko w body). Przy
    mieszance `\\def`-z-tikzem i golych tikzpicture konczy sie to
    podmienionymi obrazkami w HTML. Hoist i tak jest tu zbedny: sam
    tikzpicture jest wyciagany z body osobno.
    """
    results: list[str] = []

    def _add(definition: str) -> None:
        if r"\begin{tikzpicture}" in definition:
            return
        results.append(definition)

    # \newcommand / \renewcommand {\NAME}[args][default] <optional comment> {body}
    # 16-bzdega ma `\newcommand{\HEX}[1] % {n} (rysuje...)\n{...}` -
    # komentarz miedzy [1] a { trzeba zaakceptowac, inaczej regex chybi.
    # \renewcommand bo te same artykuly redefiniuja standardowe makra
    # (np. 16-bzdega \renewcommand{\hexagon}{...}).
    head = re.compile(
        r"\\(?:newcommand|renewcommand)\{\\\w+\}"
        r"(\[[^\]]*\])?(\[[^\]]*\])?(?:\s*%[^\n]*\n)*\s*\{"
    )
    i = 0
    while True:
        m = head.search(content, i)
        if not m:
            break
        body_start = m.end()
        depth = 1
        j = body_start
        while j < len(content) and depth > 0:
            c = content[j]
            if c == "\\" and j + 1 < len(content):
                j += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        if depth != 0:
            break
        full = content[m.start():j]
        _add(full.replace("\\newcommand", "\\providecommand", 1))
        i = j

    # \definecolor{name}{model}{spec} - 3 proste argumenty bez balansowania
    for m in re.finditer(
        r"\\definecolor\{[^}]+\}\{[^}]+\}\{[^}]+\}", content
    ):
        results.append(m.group(0))

    # \colorlet{name}{ref} - 2 proste argumenty
    for m in re.finditer(r"\\colorlet\{[^}]+\}\{[^}]+\}", content):
        results.append(m.group(0))

    # \tikzset{...} i \tikzstyle{name}=[...] - definicje stylow i pic-ow
    # trzymane w BODY artykulu, poza blokami tikzpicture (09-miskiewicz:
    # \tikzset{mmP/.pic={...}}, \tikzstyle{sArrow}=[...]). Standalone'owy
    # dokument dostaje w body tylko wyekstrahowane tikzpicture, wiec bez
    # przeniesienia ich do preambuly pdflatex sypie sie na
    # "I do not know the key '/tikz/pics/mmP'".
    head_tikzset = re.compile(r"\\tikzset\{")
    i = 0
    while True:
        m = head_tikzset.search(content, i)
        if not m:
            break
        depth = 1
        j = m.end()
        while j < len(content) and depth > 0:
            c = content[j]
            if c == "\\" and j + 1 < len(content):
                j += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        if depth != 0:
            break
        _add(content[m.start():j])
        i = j

    # \tikzstyle{name}=[...] - lista opcji moze miec ZAGNIEZDZONE nawiasy
    # kwadratowe: \tikzstyle{sArrow}=[very thick, -{Stealth[length=3mm]}, ...].
    # Naiwne [^\]]* urwaloby sie na ']' w "length=3mm]" i pdflatex leci wtedy
    # na "Paragraph ended before \tikz@style@parseA was complete".
    head_style = re.compile(r"\\tikzstyle\{[^}]*\}\s*=\s*\[")
    i = 0
    while True:
        m = head_style.search(content, i)
        if not m:
            break
        depth = 1
        j = m.end()
        while j < len(content) and depth > 0:
            c = content[j]
            if c == "\\" and j + 1 < len(content):
                j += 2
                continue
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
            j += 1
        if depth != 0:
            break
        _add(content[m.start():j])
        i = j

    # \def\name{body} bez argumentow (np. 15-rozwiazania: \def\skala{.7}).
    # Body z balansem klamerek. Pomijamy makra z #1 - te maja delimitery
    # ktore i tak nie powinny isc do tikz preambuly.
    head_def = re.compile(r"\\def\\(\w+)\{")
    i = 0
    while True:
        m = head_def.search(content, i)
        if not m:
            break
        body_start = m.end()
        depth = 1
        j = body_start
        while j < len(content) and depth > 0:
            c = content[j]
            if c == "\\" and j + 1 < len(content):
                j += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        if depth != 0:
            break
        _add(content[m.start():j])
        i = j

    return ("\n".join(results) + "\n\n") if results else ""


@log_section
def convert_images():

    content = FILE().source.tex.read_text(encoding="utf-8")
    content = wrap_overlay_centerlines(content)

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
    # zbieramy article-localne \newcommand-y (np. \putlabel w 13-rozwiazania),
    # zeby przeniesc je do preambuly standalone'owego dokumentu - inaczej
    # gubia sie przy ekstrakcji samych blokow tikzpicture, a sa w nich uzywane.
    # \providecommand zamiast \newcommand, zeby nie kolidowac z definicjami
    # z delta.sty.
    custom_macros = _extract_newcommands_as_provide(content)

    content = content.replace(
        "\\begin{document}",
        "\\definecolor{deltaColor}{HTML}{"
        + COLOR
        + "}\n\\colorlet{magenta}{deltaColor}\n\n"
        "\\providecommand{\\tg}{\\operatorname{tg}}\n"
        "\\providecommand{\\ctg}{\\operatorname{ctg}}\n"
        "\\providecommand{\\arctg}{\\operatorname{arc\\,tg}}\n"
        "\\providecommand{\\arcctg}{\\operatorname{arc\\,ctg}}\n\n"
        + custom_macros
        + "\\begin{document}",
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
    # Nie dodajemy tu osobno tikzpicture ze \scalebox: regex powyzej i tak
    # lapie ten sam tikzpicture (bez opakowania), a a3a3_replace_images numeruje
    # figureN liczac WYLACZNIE gole \begin{tikzpicture}. Wariant ze scaleboxem
    # nigdy nie zostaje wiec podlinkowany - laduje na koncu listy jako
    # osierocony, zduplikowany render (13-bzdega: figure3) i jest rsyncowany
    # na serwer. Skalowanie ze \scalebox i tak nie przechodzi przez pandoca.
    all_tikzpictures = tikzpictures
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
        # \scriptsize: rysunki maja isc mniejsza czcionka niz domyslna 10pt
        # standalone'owego dokumentu - w druku podpisy w figurach sa drobne,
        # a przy domyslnym rozmiarze po skalowaniu PNG-a do szerokosci kolumny
        # napisy w rysunku wychodza wieksze niz tekst artykulu obok.
        # Wstawiamy do CIALA dokumentu, nie do preambuly: \scriptsize to
        # przelacznik, przed \begin{document} nie ma efektu. Pojedyncze
        # tikzpicture, ktore samo ustawia sobie rozmiar, nadal wygrywa.
        doc_content = "\n\n\\scriptsize\n\n" + "\n\n".join(all_tikzpictures) + "\n\n"
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
