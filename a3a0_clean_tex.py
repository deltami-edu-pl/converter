import re
from helper import wrap_overlay_centerlines

def clean_tex(content: str) -> str | None:
    pt = "(cm|pt|px|em)"

    # owin \centerline{...\includegraphics+\llap...} w tikzpicture - inaczej pandoc
    # zgubi naklady tekstowe (raise/llap/kern). Idempotentne.
    content = wrap_overlay_centerlines(content)

    # polecenia z convert_to_html_prepare.py - usuwanie totalne
    content = re.sub(r"\n\\okladka(\[[0-9\-]*\])?\n", "\n", content)  # 2023-12 only
    content = re.sub(
        r"\\includegraphics\[[^\]]*\]\{[^\}]*kmo_logo_krzywe.png\}", "", content
    )

    content = re.sub(r"\\wd0", "0", content)
    # afiliacja inline: \hfill{\scriptsize*Wydzial...} -> \marg{Afiliacja: ...}
    # (autor uzyl bezposredniego \hfill zamiast makra \aafil; trzeba zlapac PRZED
    # stripowaniem \hfill i \scriptsize ponizej)
    content = re.sub(
        r"\\hfill\s*\{\\scriptsize\*([^}]*)\}",
        r"\\marg{Afiliacja: \1}",
        content,
    )
    # afiliacja w autorze: \waut{Autor\hfill\scriptsize\rm Instytucja}
    # -> \waut{Autor} \marg{Afiliacja: Instytucja}
    content = re.sub(
        r"\\waut\{([^}]*?)\\hfill\s*\\scriptsize\s*\\rm\s+([^}]*?)\}",
        r"\\waut{\1}\n\\marg{Afiliacja: \2}",
        content,
    )

    # afiliacja na koncu artykulu w postaci dwoch \rightline'ow w \scriptsize:
    #   {\scriptsize \rightline{Zaklad X, } \rightline{Centrum Y}}
    # -> usun z miejsca w ktorym jest, dodaj \marg{Afiliacja: Zaklad X Centrum Y}
    # zaraz po \begin{document}, zeby trafilo do gornego marginesu w HTML.
    aff_match = re.search(
        r"\{\\scriptsize\s+\\rightline\{([^}]*)\}\s+\\rightline\{\s*([^}]*)\}\s*\}",
        content,
        flags=re.DOTALL,
    )
    if aff_match:
        aff_text = (aff_match.group(1).rstrip() + " " + aff_match.group(2).strip()).strip()
        # zwin biele do pojedynczych spacji, posprzataj koncowe przecinki
        aff_text = re.sub(r"\s+", " ", aff_text)
        aff_text = re.sub(r",\s*$", "", aff_text)
        content = content[: aff_match.start()] + content[aff_match.end() :]
        content = content.replace(
            r"\begin{document}",
            r"\begin{document}" + r"\marg{Afiliacja: " + aff_text + "}",
            1,
        )

    content = re.sub(r"\\hangindent[0-9]+" + pt, "", content)
    content = re.sub(r"\\hangindent[0-9]+", "", content)
    content = re.sub(r"\\hangafter[0-9]+", "", content)
    content = re.sub(r"\\lower[0-9\.]+" + pt, "", content)
    content = re.sub(r"\\phantom1", "", content)
    content = re.sub(r"\\scalebox\{[^\}]*\}", "", content)

    content = re.sub(r"\\hsize[0-9\.]+" + pt, "", content)
    content = re.sub(r"\\noindent", "", content)
    content = re.sub(r"\\vtop", "", content)

    content = re.sub(r"\\img\[[^\]]*\]\{klub44-[^\}]*\}", "", content)
    content = re.sub(r"\\long\\def\\matematyka", "", content)
    content = re.sub(r"\\long\\def\\fizyka", "", content)
    # pandoc nie obsluguje \long\def - traci wtedy CALA tresc wywolan tej komendy.
    # zamiana na \def sprawia, ze pandoc rozwija makro normalnie.
    content = re.sub(r"\\long\\def", r"\\def", content)
    content = re.sub(r"\\matematyka", "", content)
    content = re.sub(r"\\fizyka", "", content)
    content = re.sub(r"\\klub\[[0-9]*\]\{(m|f)\}", "", content)

    # usunięcie \textsc
    content = re.sub(r"\\textsc", "", content)

    # usuniecie vspace, newpage
    content = re.sub(r"\\smallskip", "", content)
    content = re.sub(r"\\medskip", "", content)
    content = re.sub(r"\\vspace\{[^\}]*\}", "", content)
    content = re.sub(r"\\vspace\*\{[^\}]*\}", "", content)
    content = re.sub(r"\\hspace\{[^\}]*\}", "", content)
    content = re.sub(r"\\hspace\*\{[^\}]*\}", "", content)
    content = re.sub(r"\\hfill", "", content)
    content = re.sub(r"\\quad\{", "{", content)
    content = re.sub(r"\\newpage", "", content)
    content = re.sub(r"\\break", "", content)
    content = re.sub(r"\\nobreak", "", content)
    content = re.sub(r"\\fboxsep[0-9\.-]*" + pt, "", content)
    content = re.sub(r"\\rotatebox\{90\}", "", content)
    content = re.sub(r"\\raise[0-9\.-]*" + pt, "", content)
    content = re.sub(r"\\rightskip\sby[0-9\.-]*" + pt, "", content)
    content = re.sub(r"\\slash", "/", content)

    content = re.sub(r"\\spis\{[^\}]*\}\s*\{[^\}]*\}", "", content)
    content = re.sub(r"\\kospis\{[^\}]*\}\s*\{[^\}]*\}", "", content)
    content = re.sub(r"\\kpospis\{[^\}]*\}\s*\{[^\}]*\}", "", content)

    # tabulary w math display: $$ \begin{tabular}...\end{tabular} \leqno(*) $$
    # pandoc nie radzi sobie z tabular w math mode. Wyjmujemy do \begin{center},
    # \leqno(*) (lub juz przekonwertowane \tag{*}) renderujemy jako literalne (*)
    # z hfill po prawej. Uruchamia sie PRZED prepare_tex (ktore robi leqno->tag).
    content = re.sub(
        r"\$\$\s*(\\begin\{tabular\}.*?\\end\{tabular\})\s*"
        r"(?:\\leqno\s*\(\s*([^)]+?)\s*\)|\\tag\{([^}]*)\})\s*\$\$",
        lambda m: r"\begin{center}" + m.group(1) + r"\hfill(" + (m.group(2) or m.group(3)) + r")\end{center}",
        content,
        flags=re.DOTALL,
    )

    # tabulary - pandoc nie obsluguje @{...} w specach kolumn (renderuje tabele
    # jako <div class="tabular"> z surowym tekstem zamiast <table>). Strippujemy.
    def _strip_at_in_tabular(m):
        opts = m.group(1) or ""
        spec = re.sub(r"@\{[^}]*\}", "", m.group(2))
        return r"\begin{tabular}" + opts + "{" + spec + "}"
    content = re.sub(
        r"\\begin\{tabular\}(\[[^\]]*\])?\{([^}]*)\}",
        _strip_at_in_tabular,
        content,
    )
    # \multicolumn1c{...} (skrocona skladnia bez nawiasow) -> \multicolumn{1}{c}{...}
    content = re.sub(
        r"\\multicolumn(\d+)([lcr])\{", r"\\multicolumn{\1}{\2}{", content
    )
    content = re.sub(r"\\tikzstyle\{[^\}]*\}=\[[^\]\[]*\[[^\]]*\][^\]]*\]", "", content)
    content = re.sub(r"\\tikzstyle\{[^\}]*\}=\[[^\]]*\]", "", content)
    content = re.sub(r"\\resizebox\{[^\}]*\}\{[^\}]*\}", "", content)

    content = re.sub(r"\\llap", "", content)
    content = re.sub(r"\\vskip\\parskip", "", content)
    content = re.sub(r"\\looseness-[0-9]+", "", content)
    content = re.sub(r"\\arraycolsep\.[0-9]+" + pt, "", content)

    content = re.sub(r"\\begin\{multicols\}\{[0-9]+\}", "", content)
    content = re.sub(r"\\begin\{multicols\}[0-9]+", "", content)
    content = re.sub(r"\\end\{multicols\}", "", content)
    content = re.sub(r"\\setcounter\{equation\}[0-9]+", "", content)
    content = re.sub(r"\\szero[0-9\.]*" + pt, "", content)
    content = re.sub(
        r"\\spaceskip[0-9\.]+" + pt + r" minus[0-9\.]+" + pt + r"?", "", content
    )
    content = re.sub(r"\\spaceskip[0-9\.-]+" + pt, "", content)
    content = re.sub(r"\\tabcolsep\sby[0-9\-\.]+" + pt, "", content)
    content = re.sub(r"\\tabcolsep\s*[0-9\.]*" + pt, "", content)
    content = re.sub(r"\\itemsep[0-9]+" + pt, "", content)
    content = re.sub(r"\\ensuremath", "", content)

    content = re.sub(r"\\begin\{adjustwidth\}(\{[^\}]*\})?(\{[^\}]*\})?", "", content)
    content = re.sub(r"\\end\{adjustwidth\}", "", content)

    content = re.sub(r"\\centerline", "", content)

    content = re.sub(r"\\refstepcounter\{figure\}", "", content)

    content = re.sub(
        r"\\vrule\s+height\s?[\.0-9]+"
        + pt
        + r"\s+width\s?[\.0-9]+"
        + pt
        + r"(\s+depth\s?[\.0-9]+"
        + pt
        + r")?",
        "",
        content,
    )
    content = re.sub(
        r"\\vrule\s+height\s?[\.0-9]+"
        + pt
        + r"\s+depth\s?[\.0-9]+"
        + pt
        + r"(\s+width\s?[\.0-9]+"
        + pt
        + r")?",
        "",
        content,
    )
    content = re.sub(
        r"\\vrule\s+width\s?[\.0-9]+"
        + pt
        + r"\s+depth\s?[\.0-9]+"
        + pt
        + r"(\s+height\s?[\.0-9]+"
        + pt
        + r")?",
        "",
        content,
    )
    content = re.sub(
        r"\\vrule\s+width\s?[\.0-9]+"
        + pt
        + r"\s+height\s?[\.0-9]+"
        + pt
        + r"(\s+depth\s?[\.0-9]+"
        + pt
        + r")?",
        "",
        content,
    )
    content = re.sub(
        r"\\vrule\s+depth\s?[\.0-9]+"
        + pt
        + r"\s+width\s?[\.0-9]+"
        + pt
        + r"(\s+height\s?[\.0-9]+"
        + pt
        + r")?",
        "",
        content,
    )
    content = re.sub(
        r"\\vrule\s+depth\s?[\.0-9]+"
        + pt
        + r"\s+height\s?[\.0-9]+"
        + pt
        + r"(\s+width\s?[\.0-9]+"
        + pt
        + r")?",
        "",
        content,
    )

    content = re.sub(r"\\baselineskip\s+by[0-9\.\-\s]*" + pt, "", content)
    content = re.sub(
        r"\\baselineskip[^\s]*\s+plus\.[^\s]*\s+minus\.[^\s]*\s+", "", content
    )
    content = re.sub(r"\\baselineskip[^\s]*\s+plus\.[^\s]*\s+", "", content)
    content = re.sub(r"\\baselineskip[^\s]*\s+minus\.[^\s]*\s+", "", content)
    content = re.sub(r"\\baselineskip[^\s]*\s+", "", content)
    content = re.sub(r"\\parskip\s+by[0-9\.\-\s]*" + pt, "", content)
    content = re.sub(r"\\parskip[0-9\.\-\s]*" + pt, "", content)
    content = re.sub(r"\\advance", "", content)
    content = re.sub(r"\\vadjust", "", content)
    content = re.sub(r"\\goodbreak", "", content)
    content = re.sub(
        r"\\vskip\s*[\-0-9\.]*"
        + pt
        + r"\s+plus[\-0-9\.]*"
        + pt
        + r"\s+minus[\-0-9\.]*"
        + pt,
        "",
        content,
    )
    content = re.sub(
        r"\\vskip\s*[\-0-9\.]*" + pt + r"\s+plus[\-0-9\.]*" + pt, "", content
    )
    content = re.sub(r"\\vskip\s*[\-0-9\.]*" + pt, "", content)
    content = re.sub(r"\\hskip\s*[\-0-9\.]*" + pt, "", content)
    content = re.sub(r"\\medmuskip[\-0-9\.]*mu", "", content)
    content = re.sub(r"\\kern[0-9\.-]* to[0-9\.]" + pt, "", content)
    content = re.sub(r"\\kern[0-9\.-]*" + pt, "", content)
    content = re.sub(r"\\vbox to[0-9\.]" + pt, "", content)

    content = re.sub(r"\\vfill", "", content)
    content = re.sub(r"\\eject", "", content)
    content = re.sub(r"\\null", "", content)

    content = re.sub(r"\\everypar=\{[^\}]*\}", "", content)

    content = re.sub(r"\\scriptsize", "", content)
    content = re.sub(r"\\normalsize", "", content)

    # tikz
    content = re.sub(
        r"\\usetikzlibrary(\[[^\]]*\])?\{[^\}]*\}", "", content, flags=re.DOTALL
    )

    # algpseudocode
    content = re.sub(r"\\usepackage\[[^\]]*\]\{algpseudocode\}", "", content)

    content = re.sub(r"\\begin\{dwieszpalty\}", "", content)
    content = re.sub(r"\\end\{dwieszpalty\}", "", content)
    # po zdjeciu warstwy custom environments, ##1 staje sie nieprawidlowe na top
    # poziomie - pandoc nie obsluguje. Zdejmujemy poziom zagniezdzenia ##->#.
    content = re.sub(r"##(\d)", r"#\1", content)
    content = re.sub(r"\\begin\{szeroko\}", "", content)
    content = re.sub(r"\\end\{szeroko\}", "", content)
    content = re.sub(r"\\redaguje", "", content)
    # content = re.sub(r'\\Zadania', '', content)

    content = re.sub(r"\\vbox", "", content)

    # niskopoziomowy TeX-owy uklad (dimen rejestry, hbox/setbox mierzace szerokosc tabel)
    # niewidoczne w HTML, ale pandoc krztusi sie na \begin{...} w \hbox{\macro}
    content = re.sub(r"\\aboverulesep\s*[\-0-9.]*pt", "", content)
    content = re.sub(r"\\belowrulesep\s*[\-0-9.]*pt", "", content)
    content = re.sub(r"\\newdimen\s*\{\\\w+\}", "", content)
    # uwaga: dopuszczamy tylko puste argumenty {}, zeby nie zjesc \hbox z trescia
    # tekstowa (np. \hbox{\textsf{\textbf{...}}} z prawdziwego naglowka)
    content = re.sub(r"\\setbox\d+=\\hbox\{\\\w+(?:\{\})*\}", "", content)
    content = re.sub(r"\\hbox\{\\\w+(?:\{\})*\}", "", content)
    content = re.sub(r"\\setbox\d+=", "", content)
    content = re.sub(
        r"\\includegraphics(\[width=[0-9\.]+cm])?\{[^/]*/kmo_logo_krzywe-eps-converted-to.png\}",
        "",
        content,
    )

    content = re.sub(r"\\textcolor\{black\}\{\s*\}", "", content)

    return content
