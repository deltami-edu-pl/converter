import re
from dataclasses import dataclass, field
from pathlib import Path
from config import PATH

# Makra tytulow w .toc, ktore oznaczaja POZYCJE NUMERU (a nie podsekcje
# wewnatrz artykulu, np. "O obozie Math Beyond Limits" w 01-kolodziej).
ARTICLE_MACROS = {
    "poz", "ko", "kpo", "tjzwspisie", "akts", "liga", "pzn", "niebow", "zadania",
}
ZADANIA_MACRO = "zadania"
ROZWIAZANIA_STEM = "rozwiazania"


@dataclass
class Article:
    stem: str
    position: int
    page: int
    title: str
    author: str = ""
    subtitle: str = ""
    is_zadania: bool = False
    checks: dict = field(default_factory=dict)

    @property
    def html(self) -> Path | None:
        return _find(f"{self.stem}-article.html")

    @property
    def source(self) -> Path | None:
        return _find(f"{self.stem}.tex")


def _find(name: str) -> Path | None:
    """
    Artykul wedruje po katalogach w trakcie numeru: pipeline pracuje na nim
    w ROOT, `done` przenosi go dalej. Szukamy we wszystkich, zeby przeglad
    dzialal niezaleznie od tego, gdzie akurat lezy.
    """
    for folder in (PATH.ROOT, PATH.OUTPUT, PATH.DONE):
        candidate = folder / name
        if candidate.is_file():
            return candidate
    return None


def _detex(raw: str) -> str:
    r"""Tytul z .toc na czysty tekst: \penalty, \hfill \break, \emph itd."""
    out = raw
    out = re.sub(r"\\penalty\s*-?\d+\\?", " ", out)
    # cudzyslowy TeX-owe ,,X'' -> typograficzne „X”, tak jak w serwisie
    out = re.sub(r",,\s*", "\u201e", out)
    out = re.sub(r"''", "\u201d", out)
    out = re.sub(r"\\dots\b", "\u2026", out)
    out = re.sub(r"\\(hfill|break|relax|nobreakspace)\b", " ", out)
    out = re.sub(r"\\[a-zA-Z]+\s*", "", out)
    out = out.replace("{", "").replace("}", "").replace("~", " ")
    out = re.sub(r"\s+", " ", out)
    return out.strip()


def _split_groups(text: str, start: int) -> tuple[list[str], int]:
    """Kolejne grupy {...} od pozycji start; zwraca (grupy, indeks za nimi)."""
    groups: list[str] = []
    i = start
    while i < len(text) and text[i] == "{":
        depth, j = 1, i + 1
        while j < len(text) and depth:
            if text[j] == "\\":
                j += 2
                continue
            depth += (text[j] == "{") - (text[j] == "}")
            j += 1
        groups.append(text[i + 1:j - 1])
        i = j
    return groups, i


def _skip_ws(text: str, i: int) -> int:
    while i < len(text) and text[i].isspace():
        i += 1
    return i


def toc_entries() -> list[tuple[str, str, str, int, str]]:
    r"""
    Wpisy ze spisu tresci: (makro, tytul, autor, strona-druku).

    .toc jest generowany przez pdflatex razem z PDF-em numeru, wiec jest
    JEDYNYM wiarygodnym zrodlem kolejnosci i tytulow. Komentarze
    %\include{...} w glownym .tex sa nieaktualne - redakcja sklada finalny
    PDF ze wszystkim, a potem wylacza pozycje na potrzeby probnych kompilacji
    (2026-09: 04-tjz i 08-rajkowski sa zakomentowane, a sa w druku).
    """
    toc = next(PATH.SOURCE.glob("*-delta.toc"), None)
    if toc is None:
        return []

    out: list[tuple[str, str, str, int, str]] = []
    for line in toc.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\\contentsline\s*\{section\}\{", line)
        if not m:
            continue
        groups, after = _split_groups(line, m.end() - 1)
        if not groups:
            continue
        body = groups[0]
        # _split_groups zbiera wszystkie sasiadujace grupy: {tytul}{strona}{section.N}
        page = int(groups[1]) if len(groups) > 1 and groups[1].isdigit() else 0

        macro_match = re.match(r"\\([a-zA-Z]+)", body.strip())
        macro = macro_match.group(1) if macro_match else ""
        subtitle = ""
        if macro in ARTICLE_MACROS:
            stripped = body.strip()
            args, after = _split_groups(stripped, _skip_ws(stripped, len(macro) + 1))
            title = _detex(args[0]) if args else _detex(stripped)
            author = _detex(args[1]) if len(args) > 1 else ""
            # tekst PO grupach makra: \akts {Aktualnosci}\hfill \break Jeden
            # kolajder... - redakcja trzyma tam wlasciwy tytul pozycji
            subtitle = _detex(stripped[after:])
        else:
            macro, title, author = "", _detex(body), ""
        out.append((macro, title, author, page, subtitle))
    return out


def article_stems() -> list[str]:
    """Pliki NN-*.tex w dropie, w kolejnosci numerycznej."""
    stems = {
        p.stem
        for p in PATH.SOURCE.glob("[0-9][0-9]-*.tex")
        if not p.stem.startswith("00-")
    }
    return sorted(stems)


def issue_order() -> list[Article]:
    r"""
    Pozycje numeru w kolejnosci z PDF-a.

    Kolejnosc plikow NN-*.tex zgadza sie z kolejnoscia w .toc - redakcja
    numeruje pliki zgodnie z numerem. Jeden wyjatek: wpis \zadania. Tresc
    zadan jest w druku wczesniej (2026-09: str. 12, miedzy 05-gornicki
    i 06-iko), ale a1b_merge_zadania scala ja z rozwiazaniami w plik o
    NAJWYZSZYM numerze (14-rozwiazania). Dlatego \zadania mapujemy wprost na
    ten plik, a pozostale wpisy przypisujemy po kolei - inaczej pozycja zadan
    wyladowalaby na koncu numeru.
    """
    entries = [e for e in toc_entries() if e[0] in ARTICLE_MACROS]
    stems = article_stems()
    rozwiazania = next((s for s in stems if ROZWIAZANIA_STEM in s), None)
    queue = [s for s in stems if s != rozwiazania]

    out: list[Article] = []
    for macro, title, author, page, subtitle in entries:
        if macro == ZADANIA_MACRO:
            stem = rozwiazania
            if stem is None:
                continue
            title = title or "Zadania"
        else:
            if not queue:
                continue
            stem = queue.pop(0)
        out.append(Article(
            stem=stem,
            position=len(out) + 1,
            page=page,
            title=title or stem,
            author=author,
            is_zadania=(macro == ZADANIA_MACRO),
            subtitle=subtitle,
        ))

    # Artykuly dostarczone PO kompilacji PDF-a nie maja wpisu w .toc
    # (2026-09: 16-polecajka doszla osobno). Dopisujemy je na koniec, zeby
    # przeglad i publikacja ich nie pominely - strona 0 znaczy "brak w .toc".
    for stem in queue:
        out.append(Article(
            stem=stem,
            position=len(out) + 1,
            page=0,
            title=_source_title(stem) or stem,
            author="",
        ))
    return out


def _source_title(stem: str) -> str:
    r"""Tytul z \wtyt{...} w zrodle - dla artykulow bez wpisu w .toc."""
    source = _find(f"{stem}.tex")
    if source is None:
        return ""
    text = source.read_text(encoding="utf-8")
    m = re.search(r"\\wtyt\{", text)
    if not m:
        return ""
    depth, i = 1, m.end()
    while i < len(text) and depth:
        if text[i] == "\\":
            i += 2
            continue
        depth += (text[i] == "{") - (text[i] == "}")
        i += 1
    return _detex(text[m.end():i - 1])
