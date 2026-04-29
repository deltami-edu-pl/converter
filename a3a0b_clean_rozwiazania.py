import re


def clean_rozwiazania(content: str) -> str:
    r"""
    Czysci elementy specyficzne dla artykulu "rozwiazania" (lista zadan F/M):
      1. \setbox\d+=\hbox to\d+pt{\includegraphics{...kot.jpg}\hss}
         razem z \copy\d+ - zostawialo "to70pt" i obrazek kota nad sekcja
      2. \marg[-8]{... Rozwiazania na str. ...} - niepotrzebny margines
      3. \zadFiz{1143}, \zadMat{1852} - same numery zadan (wisza bez kontekstu,
         bo wlasciwa tresc jest dalej w \zadanieF/\zadanieM)
    Aplikuje sie tylko do pliku ktorego nazwa zawiera "rozwiazania".
    """
    # 1. setbox z hbox z obrazkiem kota
    content = re.sub(
        r"\\setbox\d+=\\hbox\s+to\s*\d+\s*pt\{[^{}]*\\includegraphics\{[^}]*\}[^{}]*\}",
        "",
        content,
        flags=re.DOTALL,
    )
    # \copy0 (i podobne) - referencja do boxa, ktory wlasnie skasowalismy
    content = re.sub(r"\\copy\d+", "", content)

    # 2. marginalia "Rozwiazania na str." - regex znajduje \marg ktore zawiera
    # ten tekst, potem balanced-brace wyciaga konca bloku. \marg moze miec
    # opcjonalne [..] i wewnatrz zagniezdzone klamry (np. \Magenta{\bf ...}).
    needle_marg = re.compile(
        r"\\marg(?:\[[^\]]*\])?\{",
    )
    pos = 0
    out = []
    while True:
        m = needle_marg.search(content, pos)
        if m is None:
            out.append(content[pos:])
            break
        # znajdz balanced }
        depth = 1
        i = m.end()
        while i < len(content) and depth > 0:
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
            i += 1
        block_inner = content[m.end() : i - 1]
        if re.search(r"Rozwi[ąa]zania\s+na\s+str", block_inner):
            out.append(content[pos : m.start()])
        else:
            out.append(content[pos:i])
        pos = i
    content = "".join(out)

    # 3. \zadFiz{N} i \zadMat{N} - same numery, bez tresci
    content = re.sub(r"\\zadFiz\{[^}]*\}", "", content)
    content = re.sub(r"\\zadMat\{[^}]*\}", "", content)

    # 4. \renewcommand{\Zadania}[..][..]{...} z tytulem + wywolanie {\Zadania}
    content = _strip_balanced(content, r"\\renewcommand\{\\Zadania\}(?:\[[^\]]*\])*\{")
    content = re.sub(r"\{\\Zadania\}", "", content)

    return content


def _strip_balanced(content: str, start_re: str) -> str:
    """Usun blok zaczynajacy sie od `start_re` (kandydat regex konczacy sie na `{`)
    do pasujacej balanced klamry zamykajacej. Wszystkie wystapienia."""
    pattern = re.compile(start_re)
    while True:
        m = pattern.search(content)
        if m is None:
            return content
        depth = 1
        i = m.end()
        while i < len(content) and depth > 0:
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
            i += 1
        content = content[: m.start()] + content[i:]
