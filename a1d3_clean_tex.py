import re


def strip_false_blocks(content: str) -> str:
    r"""
    Usuwa bloki \iffalse ... \fi - autorzy wylaczaja nimi fragmenty artykulu
    (16-polecajka: drugi tikzpicture). TeX takiego bloku nie wykonuje, wiec
    usuniecie jest neutralne, a bez tego a2_convert_images renderuje wylaczony
    tikzpicture do PNG i osierocony plik idzie rsynciem na serwer.

    Musi biec PRZED rename_images i przed ekstrakcja tikz, zeby ani a2, ani
    a3a3_replace_images bloku nie zobaczyly - inaczej numeracja figureN
    rozjechalaby sie miedzy nimi.

    \else jest respektowany: w \iffalse A \else B \fi aktywna jest galaz B,
    wiec zostawiamy B, a wycinamy tylko A.
    """
    # nazwa polecenia TeX konczy sie na pierwszej NIE-literze, wiec \b jest zle:
    # w "\ifnum1>0" po "m" stoi cyfra i granica slowa nie zachodzi
    token = re.compile(r"\\(iffalse|if[a-zA-Z]*|else|fi)(?![a-zA-Z])")
    out: list[str] = []
    i = 0
    while True:
        start = content.find(r"\iffalse", i)
        if start == -1:
            out.append(content[i:])
            break
        out.append(content[i:start])

        depth = 0
        else_at: int | None = None
        end: int | None = None
        for m in token.finditer(content, start):
            name = m.group(1)
            if name == "fi":
                depth -= 1
                if depth == 0:
                    end = m.end()
                    break
            elif name == "else":
                if depth == 1 and else_at is None:
                    else_at = m.end()
            else:
                depth += 1
        if end is None:
            # niedomknięty \iffalse - nie ruszamy reszty pliku
            out.append(content[start:])
            break

        if else_at is not None:
            out.append(content[else_at:end - len(r"\fi")])
        i = end
    return "".join(out)


def clean_tex(content: str) -> str:
    # usuwa zawartosc komentarzy oraz linie, w ktorych sa tylko komentarze
    content = re.sub(r"(?<=[^\\])%.*", "%", content)
    content = re.sub(r"\n([ \t]*%\n)*", "\n", content)
    content = re.sub(r"(?<=\~)\%\n", "", content, flags=re.DOTALL)

    content = re.sub(r"\\allowbreak", "", content, flags=re.DOTALL)

    # polecenia z prepare_articles - usuwanie wstępne
    content = re.sub(r"\\includeonly\{[^\}]*\}", "", content)
    content = re.sub(r"\\input\{[^\}]*\}", "", content)
    content = re.sub(r"\\input\ ?[^\\\ ]*", "", content)

    # usuwa zbędne puste linie i zostawia maksymalnie 2 puste linie
    content = re.sub(r"\n\n\n+", r"\n\n", content)

    return content


LABELED_IMAGE_RE = re.compile(
    r"\\includegraphics(?:\[[^\]]*\])?\{[^{}]+\}%?\s*"
    r"(?:\\raise-?[\d.]+pt\\llap\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}%?[ \t]*\n?[ \t]*)+"
)


def wrap_labeled_images(content: str) -> str:
    r"""
    \includegraphics{X}\raise..\llap{$A$\kern..} - etykiety nakladane na obrazek.
    Pandoc gubi pozycjonowanie i litery wypadaja pod obrazkiem, wiec calosc
    owijamy w tikzpicture: a2 renderuje ja do PNG razem z etykietami.
    """

    def wrap(m: re.Match) -> str:
        body = m.group(0).rstrip().rstrip("%")
        return r"\begin{tikzpicture}\node[inner sep=0pt]{\hbox{" + body + r"}};\end{tikzpicture}" + "\n"

    return LABELED_IMAGE_RE.sub(wrap, content)
