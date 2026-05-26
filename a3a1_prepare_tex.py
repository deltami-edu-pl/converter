import re
from config import TEXTWIDTH
from helper import log_section


@log_section
def prepare_tex(content: str) -> str:

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

    # dodaje komende, bo w ten sposob moge zmienic \marg{ na \myquote{ i nie musz szukac konca nawiasu aby wstawic \end{quote}
    content = re.sub(
        r"\\begin\{document\}",
        "\\\\newcommand{\\\\myquote}[1]{\\\\footnote{\\\\begin{quote}#1\\\\end{quote}}}\n\n\\\\begin{document}",
        content,
    )

    matches = re.findall(
        r"(\\rlap\{(\$\\Delta[^\$]*\$)\}\\href\{([^\}]+)\}\{[^\}]+\})",
        content,
        flags=re.DOTALL,
    )
    for match in matches:
        content = content.replace(
            match[0], "\\href{" + match[2] + "}{" + match[1] + "}"
        )

    matches = re.findall(
        r"(\\href\{([^\}]+)\}\{[^\}]+\}\\llap\{(\$\\Delta[^\$]*\$)\})",
        content,
        flags=re.DOTALL,
    )
    for match in matches:
        content = content.replace(
            match[0], "\\href{" + match[1] + "}{" + match[2] + "}"
        )

    content = re.sub(r"\{\\color\{red\}", "\\\\textcolor{red}{", content)

    # content = re.sub(r'\\begin\{thebibliography\}\{[A-Za-z0-9\-]*\}','\\\\begin{bibliography}', content)
    # content = re.sub(r'\\end\{thebibliography\}','\\\\end{bibliography}', content)

    if re.findall(r"\\long\\def\\matematyka", content):
        content = content.replace(
            "\\begin{document}", "\\begin{document}\\title{Klub 44}"
        )

    if re.findall(r"\\def\\pp\(\#\#1\) \{\&\#\#1\&\}", content):
        content = re.sub(r"\\def\\pp\(\#\#1\) \{\&\#\#1\&\}", "", content)
        content = re.sub(r"\\pp\(([^\)]*)\)", r"& \1 &", content)

    # zamiana \mathbbm na \mathbb
    content = content.replace("\\mathbbm", "\\mathbb")

    if re.findall(r"\\fbox", content):
        content = re.sub(
            r"\\begin\{document\}",
            "\\\\renewcommand{\\\\fbox}[1]{\\\\begin{framed}#1\\\\end{framed}}\n\\\\begin{document}",
            content,
        )

    theorems = {
        "fakt": "Fakt",
        "wniosek": "Wniosek",
        "przypuszczenie": "Przypuszczenie",
        "hipoteza": "Hipoteza",
        "aksjomat": "Aksjomat",
        "problem": "Problem",
        "pytanie": "Pytanie",
        "przyklad": "Przykład",
        "cwiczenie": "Ćwiczenie",
        "example": "Przykład",
        "przyklad": "Przykład",
        "przypadek": "Przypadek",
        "stwierdzenie": "Stwierdzenie",
        "definicja": "Definicja",
        "zadanie": "Zadanie",
        "rozwiazanie": "Rozwiązanie",
        "hint": "Wskazówka",
        "zagadka": "Zagadka",
        "wlasnosc": "Własność",
        "uwaga": "Uwaga",
        "sangaku": "Sangaku",
        "postulat": "Postulat",
        "eksperyment": "Ekspretyment",
        "solution": "rozwiazanie",
        "sposob": "Sposób",
        "twierdzenie": "Twierdzenie",
    }

    for key in theorems:
        name = theorems[key]
        if re.findall(r"\\begin\{" + key + r"\*?\}", content):
            content = content.replace(
                "\\begin{document}",
                "\\newtheorem{"
                + key
                + "}{"
                + name
                + "}\n\\newtheorem{"
                + key
                + "*}{"
                + name
                + "}\n\n\\begin{document}",
            )
            content = re.sub(
                r"(\\begin\{" + key + r"\*?\}(\s*\[[^\]]*\])?)", r"\1{\\em", content
            )
            content = re.sub(r"(\\end\{" + key + r"\*?\})", r"}\1", content)

    content = re.sub(r"\\aafil(\[[^\]]*\])?\{(?=\s*Kontakt[:\s])", "\\\\marg{", content)
    content = re.sub(r"\\aafil(\[[^\]]*\])?\{", "\\\\marg{Afiliacja: ", content)
    content = re.sub(r"(\\color\{[a-zA-Z0-9]+\})([^{]*?)(?=})", r"\1{\2}", content)
    content = re.sub(r"\\color\{magenta\}", "\\\\textcolor{deltaColor}", content)
    content = re.sub(r"\\textcolor\{magenta\}", "\\\\textcolor{deltaColor}", content)
    content = re.sub(r"\\Magenta\s?\{", "\\\\textcolor{deltaColor}{ ", content)
    content = re.sub(r"\\quad", "\\\\ \\\\ \\\\ ", content)
    content = re.sub(r"\\qquad", "\\\\ \\\\ \\\\ ", content)

    content = re.sub(r"(?<=[^\$\\])\$,", ",$", content)
    content = re.sub(r"(?<=[^\$\\])\$\.", ".$", content)

    if re.findall(r"\\ip\{", content):
        content = re.sub(
            r"\\begin\{document\}",
            "\\\\newcommand{\\\\ip}[2]{\\\\langle #1,#2 \\\\rangle}\n\n\\\\begin{document}",
            content,
        )
    if re.findall(r"\\ip\{", content):
        content = re.sub(
            r"\\begin\{document\}",
            "\\\\newcommand{\\\\op}[2]{\\\\ket{#1}\\\\bra{#2}}\n\n\\\\begin{document}",
            content,
        )

    content = re.sub(r"\\xhref{", "\\\\href{", content)
    content = re.sub(r"\\xxhref{", "\\\\href{", content)

    content = re.sub(r"\\textbullet\{\}", "$\\\\bullet$", content)

    content = re.sub(r"\\begin\{mdframed\}", "\\\\begin{framed}", content)
    content = re.sub(r"\\end\{mdframed\}", "\\\\end{framed}", content)

    # content = re.sub(r'(<!\\def)\\pp', '\\\\pp{}', content)
    # content = re.sub(r'\\def\\pp\#1\ ', '\\\\def\\\\nieumiemregex#1', content) # don't ask
    # content = re.sub(r'\\pp', '\\\\pp{}', content) # don't ask
    # content = re.sub(r'nieumiemregex', 'pp', content) # don't ask

    content = re.sub(r"\\sb", "_", content)
    content = re.sub(r"\\sp(>=[0-9])", "^", content)

    content = re.sub(r"\\Black\{", "{", content)

    content = re.sub(r"\\rlap\{", "{", content)
    content = re.sub(r"\\dc ", ",,", content)
    content = re.sub(r"\\endinput.*", "\\\\end{document}", content, flags=re.DOTALL)
    content = re.sub(r"(?<!\$)(\\eqref\{[^\}]+\})", r"$\1$", content)

    content = re.sub(r"=\\newline=", r"=", content)

    # i=1
    # matches = re.findall(r'(\\begin\{equation\}(.*?\\label.*?\\end\{equation\}))', content, flags=re.DOTALL)
    # for match in matches:
    #     if not "\\tag" in match[0]:
    #         content = content.replace(match[0], "\\begin{equation}\\tag{"+str(i)+"}"+match[1])
    #         i=i+1

    matches = re.findall(
        r"(\\includegraphics\[width=([0-9\.]+)(pt|cm|px|in)\])", content
    )
    for match in matches:
        newtext = (
            "\\includegraphics[width="
            + str(int(float(match[1]) * 1.5))
            + match[2]
            + "]"
        )
        content = content.replace(match[0], newtext)

    matches = re.findall(r"(\\includegraphics\[width=([0-9\.]+)\\textwidth\])", content)
    for match in matches:
        newtext = (
            "\\includegraphics[width="
            + str(int(float(match[1]) * TEXTWIDTH * (1.5)))
            + "pt]"
        )
        content = content.replace(match[0], newtext)

    matches = re.findall(
        r"(\$\$\s*\{*\s*(\\includegraphics(\[[^\]]*\])?\{([^\}]*)\})\s*\}*\s*\$\$)",
        content,
        flags=re.DOTALL,
    )
    for match in matches:
        content = content.replace(
            match[0], "\\begin{center}" + match[1] + "\\end{center}"
        )

    content = re.sub(r"\\marg\s*\{", "\\\\myquote{", content)
    content = re.sub(r"\\marg\[[^\]]*\]\s*\{", "\\\\myquote{", content)
    content = re.sub(r"\\marginpar\{", "\\\\myquote{", content)

    # tytuły
    if content.find("\\wtyt") == -1:
        content = re.sub(r"\\mtyt", "\\\\wtyt", content, count=1)
    content = re.sub(r"\\wtyt\{", "\\\\" + "title{", content)

    # autor
    author_match = re.match(
        r"^.*(\\waut\{(\s*\\color\{black\}\s*)?([^\}]*)\}).*$", content, flags=re.DOTALL
    )
    if author_match is not None:
        author = author_match.group(3)
        content = content.replace(author_match.group(1), "")
        content = content.replace(
            "\\begin{document}", "\\begin{document}\\author{" + author + "}"
        )
    else:
        if content.find("\\waut") == -1:
            author_matches = re.findall(
                r"(\\rightline{\s*\\large\s*\{\}\s*\\textit\{([^\}]*)\}\s*(\{\})*\s*\})",
                content,
                flags=re.DOTALL,
            )
            if len(author_matches) == 0:
                author_matches = re.findall(
                    r"(\\rightline{\s*\\large\s*\\textit\{([^\}]*)\}\s*(\{\})*[\s\%]*\})",
                    content,
                    flags=re.DOTALL,
                )
            if len(author_matches) == 0:
                author_matches = re.findall(
                    r"(\\rightline{\s*\\large\s*\\it\s*([^\\]*)\s*(\\ )*[\\a-z]*\(\{[a-z\.\@\\\s]*\}\s*\)\s*\})",
                    content,
                    flags=re.DOTALL,
                )
            if len(author_matches) == 0:
                author_matches = re.findall(
                    r"(\\rightline{\s*\\large\s*\\it\s*([^\}]*)\s*(\{\})*[\s\%]*\})",
                    content,
                    flags=re.DOTALL,
                )
            if len(author_matches) == 0:
                author_matches = re.findall(
                    r"(\\rightline{\s*\\textit\{\s*([^\}]*)\s*\}\})",
                    content,
                    flags=re.DOTALL,
                )
            for author_match in author_matches:
                author = author_match[1]
                content = content.replace(author_match[0], "\\waut{" + author + "}")
                print("AUTOR: " + author)
    content = re.sub(r"\\waut\{", "\\\\author{", content)

    # affil weird
    content = content.replace(
        "{\\scriptsize\\rm Uniwersytet im. A. Mickiewicza w~Poznaniu}",
        "\\myquote{Uniwersytet im. A. Mickiewicza w~Poznaniu}",
    )

    affil_matches = re.findall(
        r"(\\rightline\{\s*\\scriptsize\s*([^\}]*)\s*\})", content, flags=re.DOTALL
    )
    if len(affil_matches) > 0:
        for affil_match in affil_matches:
            affil = affil_match[1]
            print("AFFIL: " + affil)
            content = content.replace(affil_match[0], "")
            content = content.replace(
                "\\begin{document}", "\\begin{document}\\myquote{" + affil + "}"
            )
    else:
        affil_matches = re.findall(
            r"(\{\s*\\scriptsize\s\\rightline\{([^\}]*)\}\s*\\rightline\{([^\}]*)\}\s*\\rightline\{([^\}]*)\}(\s*\\par)?\s*\})",
            content,
            flags=re.DOTALL,
        )
        if len(affil_matches) > 0:
            for affil_match in affil_matches:
                affil = (
                    affil_match[1] + "\\\\" + affil_match[2] + "\\\\" + affil_match[3]
                )
                print("AFFIL: " + affil)
                content = content.replace(affil_match[0], "")
                content = content.replace(
                    "\\begin{document}", "\\begin{document}\\myquote{" + affil + "}"
                )
        else:
            affil_matches = re.findall(
                r"(\{\s*\\scriptsize\s\\rightline\{([^\}]*)\}\s*\\rightline\{([^\}]*)\}(\s*\\par)?\s*\})",
                content,
                flags=re.DOTALL,
            )
            if len(affil_matches) > 0:
                for affil_match in affil_matches:
                    affil = affil_match[1] + "\\\\" + affil_match[2]
                    print("AFFIL: " + affil)
                    content = content.replace(affil_match[0], "")
                    content = content.replace(
                        "\\begin{document}", "\\begin{document}\\myquote{" + affil + "}"
                    )
            else:
                affil_matches = re.findall(
                    r"(\{\s*\\scriptsize\s\\rightline\{([^\}]*)\}(\s*\\par)?\s*\})",
                    content,
                    flags=re.DOTALL,
                )
                for affil_match in affil_matches:
                    affil = affil_match[1]
                    print("AFFIL: " + affil)
                    content = content.replace(affil_match[0], "")
                    content = content.replace(
                        "\\begin{document}", "\\begin{document}\\myquote{" + affil + "}"
                    )
    # END affil weird

    content = re.sub(r"\\rightline\{", "\\\\myquote{", content)

    content = re.sub(r"\\mtyt\{", "\\\\subsection*{", content)
    content = re.sub(r"\\wtyt\{", "\\\\subsection*{", content)
    content = re.sub(r"\\styt\{", "\\\\subsection*{", content)
    content = re.sub(r"\\ptyt\{", "\\\\subsection*{", content)

    content = re.sub(r"\\znztyt\{[0-9]+\}\{", "\\\\title{", content)
    content = re.sub(r"\\tjztyt\{", "\\\\title{", content)
    content = re.sub(r"\\pzntyt\{", "\\\\title{", content)
    content = re.sub(r"\\niebowtyt\{", "\\\\title{", content)

    if re.search(r"\\mathcode`\\,=\"013B", content):
        content = re.sub(r"\\mathcode`\\,=\"013B", "", content)
        content = re.sub(r"(?<!\\),", "{,}", content)

    # dodane przeze mnie - Janek

    # usuniecie xleft, zwykle z ligi
    content = re.sub(r"\\def\\xleft#1\\right\{#1\}", "", content)
    content = re.sub(r"\\xleft\b", r"\\left", content)

    # naprawa cudzysłowów - na polskie
    content = re.sub(r"(^|[\s\(\[\{—–])\s*,,(?=\S)", r"\1„", content)
    content = re.sub(r"''", "”", content)

    # zamiana \ref na \eqref i usunięcie okalających nawiasów
    content = re.sub(r"\(\s*\\ref\{([^}]+)\}\s*\)", r"\\eqref{\1}", content)

    # zamiana \leqno(1) na \tag{1}
    content = re.sub(
        r"\\leqno\s*\(\s*([^)]+?)\s*\)", r"\\tag{\1}", content, flags=re.DOTALL
    )

        # dodanie polecenia \dv, bo pakiet physics nie działa w MathJax
    if content.find("\\dv") != -1:
        doc_start = content.find("\\begin{document}")
        if doc_start != -1:
            newcommand = r"\newcommand{\dv}[2]{\frac{\mathrm d #1}{\mathrm d #2}}" + "\n\n"
            content = content[:doc_start] + newcommand + content[doc_start:]

    return content
