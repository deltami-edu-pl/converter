import re
from helper import wrap_overlay_centerlines

def clean_tex(content: str) -> str | None:
    pt = "(cm|pt|px|em)"

    # owin \centerline{...\includegraphics+\llap...} w tikzpicture - inaczej pandoc
    # zgubi naklady tekstowe (raise/llap/kern). Idempotentne.
    content = wrap_overlay_centerlines(content)
    content = expand_counters(content)
    # pandoc gubi \framebox/\fbox RAZEM z obrazkiem w srodku (2026-12: skan u Gornickiego)
    content = re.sub(r"\\f(?:rame)?box\{\s*(\\includegraphics(?:\[[^\]]*\])?\{[^{}]*\})\s*\}", r"\1", content)
    # wymiar z przecinkiem dziesietnym (\hsize5,5cm) - TeX przyjmuje, regexy nizej nie
    content = re.sub(
        r"(\\(?:[hv]size|kern|[hv]skip|raise|lower|parindent|hangindent)\s*-?\d+),(\d+\s*(?:pt|cm|mm|em|ex|in))",
        r"\1.\2",
        content,
    )
    content = re.sub(r"(\\[hv]space\*?\{\s*-?\d+),(\d+)", r"\1.\2", content)
    content = re.sub(r"\\marg(\[[^\]]*\])?\{\s*\}", "", content)
    # \cai{N} w tytule - etykieta serii bez kotwicy w tekscie trafia na koniec marginesu
    content = re.sub(r"(\\wtyt\{[^{}]*?)\\(?:cai|ai)\{\d+\}", r"\1", content)
    content = strip_klub44_logo_margins(content)
    content = re.sub(r"\\textdegree\b\s*", "°", content)
    # symbol z podpisem nakladanym \ooalign (MathJax nie zna) -> \underset
    content = re.sub(
        r"\\ooalign\{\\hfil\s*(.+?)\\hfil\\cr\\hfil\\raisebox\{[^}]*\}\{\$\\scriptstyle\s*(.+?)\$\}\\hfil\\cr\}",
        r"\\underset{\2}{\1}",
        content,
    )
    content = re.sub(
        r"\\begin\{enumerate\}\[\s*start\s*=\s*(\d+)\s*\]",
        lambda m: r"\begin{enumerate}\setcounter{enumi}{" + str(int(m.group(1)) - 1) + "}",
        content,
    )

    # Zlamana linia w opcjonalnym argumencie \includegraphics: pandoc przerywa
    # parsowanie w srodku [...] i myli sie o kilkanascie linii dalej (2026-10,
    # 03-gladczuk: "unexpected \footnote expecting \end{quote}" wskazywalo na
    # \myquote, a winne bylo [\n width=4cm]). Autorzy lamia opcje dla
    # czytelnosci zrodla, wiec sklejamy je w jedna linie. Ruszamy wylacznie
    # nawias opcji - sciezka w {...} zostaje nietknieta. Robimy to przed
    # pozostalymi regexami na \includegraphics, bo one zakladaja jedna linie.
    content = re.sub(
        r"\\includegraphics\s*\[([^\]]*)\]\s*\{",
        lambda m: "\\includegraphics[" + re.sub(r"\s+", " ", m.group(1)).strip() + "]{",
        content,
    )

    # MetaPost: a1c_prepare_images konwertuje got/**/*.mps do PNG-a o tej samej
    # nazwie, wiec referencja w tresci musi isc za tym. Przegladarka .mps nie
    # otworzy (2026-10: 39 martwych obrazkow w 07-ciesla i 08-jankowski).
    content = re.sub(
        r"(\\includegraphics(?:\[[^\]]*\])?\{[^}]*)\.mps\}",
        r"\1.png}",
        content,
    )

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

    # afiliacja jako osobna grupa pod \waut: {\hfill\scriptsize\rm Instytucja}
    # (autor Bzdęga: \waut{...}\n{\hfill\scriptsize\rm Uniwersytet...})
    # bez tej reguly \hfill i \scriptsize zostaja zestripowane (linie 86, 265),
    # a tekst afiliacji wlatuje do body jako pierwszy akapit. Lapiemy PRZED
    # stripowaniem.
    content = re.sub(
        r"\{\\hfill\s*\\scriptsize\s*\\rm\s+([^}]*)\}",
        r"\\marg{Afiliacja: \1}",
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

    # afiliacja na koncu jako jeden \rightline z gwiazdka (Prosto z nieba):
    #   {\scriptsize \rightline{*Zaklad X, Centrum Y}}  -> gorny margines
    aff_match = re.search(
        r"\{\\scriptsize\s*\\rightline\{\s*\*([^}]*)\}\s*\}", content, flags=re.DOTALL
    )
    if aff_match:
        aff_text = re.sub(r"\s+", " ", aff_match.group(1).replace("%", "")).strip()
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
    content = re.sub(r"\\scalebox\{[^\}]*\}(\[[^\]]*\])?", "", content)

    content = re.sub(r"\\hsize[0-9\.]+" + pt, "", content)
    content = re.sub(r"\\noindent", "", content)
    content = re.sub(r"\\vtop", "", content)

    # \parskip\smallskipamount, \baselineskip12pt plus.2pt minus.2pt,
    # \rightskip10pt minus20pt - TeX-owe przypisania rejestrow dlugosci.
    # Pandoc ich nie ogarnia, wyciekaja do HTML jako goly tekst.
    content = re.sub(r"\\parskip\s*\\\w*skipamount\b", "", content)
    content = re.sub(
        r"\\(?:parskip|baselineskip|lineskip|topskip|rightskip|leftskip)\s*[\-0-9.]+"
        + pt
        + r"(?:\s+(?:plus|minus)\s*[\-0-9.]+" + pt + r")*",
        "",
        content,
    )

    # \hbox to18cm{...} / \vbox to84pt{...} - boxy z dokladnie zadanym
    # rozmiarem. Pandoc/HTML nie ma pojecia o "to NN cm", strippujemy sam
    # prefiks "to<dimen>", zostawiajac samo \hbox/\vbox. \! - negatywna
    # cienka spacja, wycieka jako tekst.
    content = re.sub(r"\\([hv])box\s+to\s*[\-0-9.]+" + pt, r"\\\1box", content)
    content = re.sub(r"\\([hv])box\s+to\s*\\[hv]size", r"\\\1box", content)
    content = re.sub(r"\\!", "", content)

    # \hbox{00.\enskip}, \hbox{00.--00.\enskip} - pomocnicze boxy mierzace
    # szerokosc dla \xitem/\xxitem (\wd0, \wd1). Bez tych makr beztreciowe.
    content = re.sub(r"\\hbox\{[0-9.\-\s]*\\enskip\}", "", content)

    # \def\NAME#1<delim>...{...} - TeX-owe makra z delimiterami w argumentach
    # (np. 07-olimpiady ma \def\zz#1 #2,{...}, \def\xitem#1. {...}, \def\pp#1.
    # #2,{...}). Pandoc nie umie sparsowac tej skladni. Wykrywamy wszystkie
    # nazwy makr po tym wzorcu, wycinamy definicje i sciagamy prefiks z wywolan
    # zeby przezyl tekst miedzy nimi.
    delim_macros = set(re.findall(
        r"\\def\\([a-zA-Z]+)#1[^{a-zA-Z#]", content
    ))
    for macro in delim_macros:
        # parsujemy definicje \def\NAME#1<delim>{<body>}, wyciagajac delim i
        # body z balansem klamerek. Jezeli delim to control sequence (np.
        # \right), umiemy rozwinac wywolania \NAME<X><delim> -> body[#1:=X]
        # zanim wytniemy def.
        head_match = re.search(
            rf"\\def\\{macro}#1([^{{]*?)\{{",
            content,
        )
        body: str | None = None
        delim: str | None = None
        if head_match:
            raw_delim = head_match.group(1).strip()
            if raw_delim.startswith("\\"):
                delim = raw_delim
                body_start = head_match.end()
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
                        if depth == 0:
                            body = content[body_start:j]
                            break
                    j += 1

        # usun definicje
        content = re.sub(
            rf"\\def\\{macro}#1[^{{]*\{{[^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*\}}",
            "",
            content,
        )

        if body is not None and delim is not None:
            # \NAME<X><delim> -> body z #1 zastapionym przez <X>
            def _expand(m: re.Match, _body=body) -> str:
                return _body.replace("#1", m.group(1))
            # TeX rozwija makra z delimiterem ITERACYJNIE: po podstawieniu
            # zagnieżdżone wywołanie widzi już nowy delimiter. re.sub robi
            # jedno przejscie i skanuje dalej ZA dopasowaniem, wiec zagniezdzone
            # \NAME, ktore wpadlo do #1, nigdy nie bylo rozwijane - zostawal
            # osierocony \right i MathJax renderowal cala formule na czerwono
            # (02-gos: \bbleft(\lfloor\bbleft(...\right)...\right)).
            # Powtarzamy wiec do wyczerpania, z limitem na wypadek patologii.
            for _ in range(20):
                content, n_sub = re.subn(
                    rf"\\{macro}(.*?){re.escape(delim)}",
                    _expand,
                    content,
                    flags=re.DOTALL,
                )
                if n_sub == 0:
                    break
            else:
                print(
                    f"- !!! \\{macro}: rozwijanie nie zbieglo sie w 20 iteracjach"
                    " - sprawdz formule w HTML"
                )

        # \MACRO<liczba>. -> <liczba>. (np. \xitem1. -> 1.); zachowuje
        # widoczna numeracje. Musi byc PRZED ogolnym stripem \MACRO\b.
        content = re.sub(rf"\\{macro}(\d+)\.\s*", r"\1. ", content)
        content = re.sub(rf"\\{macro}\b\s*", "", content)

    content = re.sub(r"\\img\[[^\]]*\]\{klub44-[^\}]*\}", "", content)
    content = inline_section_bodies(content, ("matematyka", "fizyka"))
    content = re.sub(r"\\long\\def\\matematyka", "", content)
    content = re.sub(r"\\long\\def\\fizyka", "", content)
    # pandoc nie obsluguje \long\def - traci wtedy CALA tresc wywolan tej komendy.
    # zamiana na \def sprawia, ze pandoc rozwija makro normalnie.
    content = stack_layout_macros(content)
    content = re.sub(r"\\long\\def", r"\\def", content)
    content = re.sub(r"\\matematyka", "", content)
    content = re.sub(r"\\fizyka", "", content)
    content = re.sub(r"\\klub\[[0-9]*\]\{(m|f)\}", "", content)

    # usunięcie \textsc
    content = re.sub(r"\\textsc", "", content)

    # usuniecie vspace, newpage
    # \let\X\Y (i \let\X=\Y) - TeX-owe aliasowanie komend, np.
    # 07-olimpiady: \let\medskip\smallskip. Musi zniknac PRZED stripami
    # \smallskip/\medskip ponizej, inaczej zostawiamy sam \let bez argumentow
    # i pandoc wybucha.
    content = re.sub(r"\\let\s*\\\w+\s*=?\s*\\\w+", "", content)

    content = re.sub(r"\\smallskip\b", "", content)
    content = re.sub(r"\\medskip\b", "", content)
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
    # \rotatebox{kat}{tresc} - pandoc gubi rotatebox RAZEM z trescia. Strippujemy
    # samo polecenie zostawiajac {tresc} jako kolejny argument do dalszej obrobki.
    content = re.sub(r"\\rotatebox\{[^}]*\}", "", content)
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
    # \vskip / \hskip, gdzie wymiar jest rejestrem dlugosci, nie liczba:
    # \vskip\parskip, \vskip-\parskip (07-kat-o), \hskip -\baselineskip.
    # Bez tego pandoc wywala sie na "unexpected \parskip".
    content = re.sub(r"\\(?:vskip|hskip)\s*-?\s*\\[a-zA-Z]+", "", content)
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
        + r"(\s+depth\s?-?[\.0-9]+"
        + pt
        + r")?",
        "",
        content,
    )
    content = re.sub(
        r"\\vrule\s+height\s?[\.0-9]+"
        + pt
        + r"\s+depth\s?-?[\.0-9]+"
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
        + r"\s+depth\s?-?[\.0-9]+"
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
        + r"(\s+depth\s?-?[\.0-9]+"
        + pt
        + r")?",
        "",
        content,
    )
    content = re.sub(
        r"\\vrule\s+depth\s?-?[\.0-9]+"
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
        r"\\vrule\s+depth\s?-?[\.0-9]+"
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
    # \vskip / \hskip z pelnym glue: <dimen> [plus <dimen>] [minus <dimen>],
    # w dowolnej kombinacji i kolejnosci. Wczesniej byly tu osobne warianty
    # (plus+minus, plus, sam dimen) i "\vskip38pt minus5pt" (03-tjz) przechodzil
    # tylko czesciowo - zostawal goly "minus5pt" jako akapit w HTML.
    content = re.sub(
        r"\\(?:vskip|hskip)\s*[\-0-9\.]*"
        + pt
        + r"(?:\s*(?:plus|minus)\s*[\-0-9\.]*" + pt + r")*",
        "",
        content,
    )
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
    content = re.sub(r"\\redaguje\s*\{", r"\\marg{", content)
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
    # \hbox{\macro} - tylko zdejmujemy wrapper, zeby \macro (np. \rysa
    # rozwijajaca sie do \includegraphics) trafil dalej do pandoca; pandoc i tak
    # \hbox{} ignoruje
    content = re.sub(r"\\hbox\{(\\\w+(?:\{\})*)\}", r"\1", content)
    content = re.sub(r"\\global\s*\\setbox", r"\\setbox", content)
    content = re.sub(r"\\setbox\d+=", "", content)
    content = re.sub(r"\\marg\{Afiliacja:\s*\*\s*", r"\\marg{Afiliacja: ", content)
    content = re.sub(r"\\box\d+(?![0-9])", "", content)
    content = re.sub(
        r"\\includegraphics(\[width=[0-9\.]+cm])?\{[^/]*/kmo_logo_krzywe-eps-converted-to.png\}",
        "",
        content,
    )

    content = re.sub(r"\\textcolor\{black\}\{\s*\}", "", content)

    return content


LAYOUT_DEF_RE = re.compile(r"(?:\\long)?\\def\\([a-zA-Z]+)((?:#\d)+)\{")


def stack_layout_macros(content: str) -> str:
    r"""
    \def\dwa#1#2{\hbox to\hsize{\parbox{..}{#1}\hfill\parbox{..}{#2}}} - kolumny
    obok siebie w druku. Pandoc nie przetworzy boxow z blokami (itemize) w srodku,
    wiec na webie argumenty ida jeden pod drugim.
    """
    out, pos = [], 0
    for m in LAYOUT_DEF_RE.finditer(content):
        if m.start() < pos:
            continue
        depth, j = 1, m.end()
        while j < len(content) and depth:
            if content[j] == "\\":
                j += 2
                continue
            depth += {"{": 1, "}": -1}.get(content[j], 0)
            j += 1
        body = content[m.end() : j - 1]
        if "\\parbox" not in body:
            continue
        args = "\n\n".join(re.findall(r"#\d", m.group(2)))
        out.append(content[pos : m.start()])
        out.append(f"\\def\\{m.group(1)}{m.group(2)}{{{args}}}")
        pos = j
    out.append(content[pos:])
    return "".join(out)


COUNTER_TOKEN_RE = re.compile(
    r"\\setcounter\{(\w+)\}\s*\{?\s*(-?\d+)\s*\}?|\\(?:ref)?stepcounter\{(\w+)\}|\\the([a-zA-Z]+)"
)


def expand_counters(content: str) -> str:
    r"""
    Wlasne liczniki autora (\newcounter{rys}, \setcounter{rys}1, Rys. \therys
    \stepcounter{rys}) - pandoc ich nie liczy: podpisy wychodzily jako "Rys."
    bez numeru, a \setcounter{rys}1 wyciekal jako "1". Liczymy sekwencyjnie.
    """
    names = set(re.findall(r"\\newcounter\{(\w+)\}", content))
    if not names:
        return content
    values = {name: 0 for name in names}

    def step(m: re.Match) -> str:
        if m.group(1) in names:
            values[m.group(1)] = int(m.group(2))
            return ""
        if m.group(3) in names:
            values[m.group(3)] += 1
            return ""
        if m.group(4) in names:
            return str(values[m.group(4)])
        return m.group(0)

    content = re.sub(r"\\newcounter\{(" + "|".join(map(re.escape, names)) + r")\}", "", content)
    return COUNTER_TOKEN_RE.sub(step, content)


def strip_klub44_logo_margins(content: str) -> str:
    """\\marg{..Klub 44 M.. \\includegraphics{..klub44-m..}} - naglowek z logo ligi, na webie zbedny."""
    out, pos = [], 0
    for m in re.finditer(r"\\marg(?:\[[^\]]*\])?\{", content):
        if m.start() < pos:
            continue
        end = m.end()
        depth = 1
        while end < len(content) and depth:
            if content[end] == "\\":
                end += 2
                continue
            depth += {"{": 1, "}": -1}.get(content[end], 0)
            end += 1
        if "klub44-" in content[m.end() : end]:
            out.append(content[pos : m.start()])
            pos = end
    out.append(content[pos:])
    return "".join(out)


def inline_section_bodies(content: str, names: tuple[str, ...]) -> str:
    r"""
    \long\def\matematyka{...} ... {\fizyka} {\matematyka} - Liga definiuje bloki
    na gorze pliku, a wywoluje w kolejnosci druku. Bez tego tresc zostawala w
    miejscu definicji i kolejnosc dzialow byla odwrocona.
    """
    for name in names:
        m = re.search(rf"\\long\\def\\{name}\s*\{{", content)
        if not m:
            continue
        depth, j = 1, m.end()
        while j < len(content) and depth:
            if content[j] == "\\":
                j += 2
                continue
            depth += {"{": 1, "}": -1}.get(content[j], 0)
            j += 1
        body = content[m.end() : j - 1]
        rest = content[: m.start()] + content[j:]
        call = re.search(rf"\{{\s*\\{name}\s*\}}|\\{name}(?![a-zA-Z])", rest)
        if call is None:
            continue
        content = rest[: call.start()] + body + rest[call.end() :]
    return content
