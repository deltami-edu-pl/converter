import re

# Po czym poznajemy, ze \def\NAME#1{...} jest makrem podpisu pod rysunkiem.
# Redakcja nazywa je roznie w roznych artykulach (\rys, \podpis, ...), ale
# body zawsze kreci sie wokol licznika "rys" albo doslownego "Rys.".
CAPTION_DEF_MARKERS = (
    "Rys.",                     # \def\rys#1{\medskip{\scriptsize Rys. #1\par}}
    r"\therys",
    r"\thefigure",
    r"\refstepcounter{rys}",
    r"\refstepcounter{figure}",
)

# Historyczna nazwa makra podpisu. Stara wersja tego modulu usuwala linie
# z \def\rys#1{...} BEZWARUNKOWO, wiec traktujemy ja jak makro podpisu nawet
# gdy body nie pasuje do zadnego markera - inaczej definicja zostalaby w tresci
# i wyciekla do HTML-a jako goly tekst.
LEGACY_CAPTION_NAME = "rys"


def _find_balanced(content: str, open_pos: int) -> int:
    """Indeks ZA klamra domykajaca grupe otwarta na `open_pos` ('{'). -1 gdy brak."""
    depth = 1
    i = open_pos + 1
    while i < len(content) and depth > 0:
        ch = content[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    return i if depth == 0 else -1


def _caption_macro_names(content: str) -> tuple[set[str], str]:
    r"""
    Znajduje nazwy makr podpisow zdefiniowanych w artykule i usuwa ich
    definicje z tresci. Zwraca (nazwy, tresc-bez-definicji).

    Pandoc nie rozwija takich \def-ow: zostawia sama linie definicji jako
    goly tekst, a wszystkie WYWOLANIA po cichu wyrzuca - wiec bez tego
    kroku podpisy pod rysunkami znikaja z HTML-a (01-makowska: \podpis).
    """
    names: set[str] = set()
    spans: list[tuple[int, int]] = []

    for m in re.finditer(r"\\def\\([a-zA-Z]+)#1\s*\{", content):
        open_pos = content.rindex("{", m.start(), m.end())
        end = _find_balanced(content, open_pos)
        if end == -1:
            continue
        body = content[open_pos:end]
        if m.group(1) == LEGACY_CAPTION_NAME or any(
            marker in body for marker in CAPTION_DEF_MARKERS
        ):
            names.add(m.group(1))
            spans.append((m.start(), end))

    for start, end in reversed(spans):
        content = content[:start] + content[end:]

    return names, content


def expand_rys_captions(content: str) -> str:
    r"""
    1. Wykrywa i usuwa definicje makr podpisow (\def\rys#1{...},
       \def\podpis#1{...} - rozpoznawane po zawartosci body, nie po nazwie).
    2. Zamienia wszystkie ich wywolania na:
         Rys. N. ...
       z poprawnym ogarnieciem zagniezdzonych klamerek (np. \cite{...}).

    Numeracja idzie w kolejnosci wystepowania w dokumencie, wspolnym licznikiem
    dla wszystkich makr podpisu (artykul moze uzywac wiecej niz jednego).
    """
    names, content = _caption_macro_names(content)
    names.add(LEGACY_CAPTION_NAME)  # \rys moze byc uzyte bez definicji w artykule

    # Wywolania wszystkich makr podpisu, przetwarzane w kolejnosci pozycji,
    # zeby numeracja zgadzala sie z kolejnoscia rysunkow w tekscie.
    call_re = re.compile(r"\\(?:" + "|".join(sorted(map(re.escape, names))) + r")\{")

    result_parts: list[str] = []
    i = 0
    counter = 1

    while True:
        m = call_re.search(content, i)
        if m is None:
            result_parts.append(content[i:])
            break

        result_parts.append(content[i : m.start()])

        open_pos = m.end() - 1
        end = _find_balanced(content, open_pos)
        if end == -1:
            # brak domykajacej klamry - nie ruszamy dalszego tekstu
            result_parts.append(content[m.start() :])
            break

        caption = content[open_pos + 1 : end - 1].strip()
        result_parts.append(f"Rys. {counter}. {caption}")
        counter += 1
        i = end

    return "".join(result_parts)
