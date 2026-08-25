#!/usr/bin/env python3
"""
Lista adresow artykulow do Paper doca "Delta - wydanie online".

DOMYSLNIE nie zapisuje nic na Dropboksie, tylko generuje gotowy fragment.
Powod: nowa sekcja trafia na GORE listy, czyli w srodek dokumentu, co
wymagaloby polityki `overwrite` - przeslania calej tresci z powrotem.
Starsze sekcje zawieraja obrazki i notatki, a round-trip przez markdown
moze je uszkodzic. Wklejenie jednego bloku raz na numer jest tansze niz
ryzyko rozwalenia archiwum linkow.

Kolejnosc jest ta z DRUKU (z .toc), nie z nazw plikow - w dotychczasowych
wpisach zadania ladowaly na pozycji pliku 14-rozwiazania zamiast tam, gdzie
sa w numerze.
"""

import argparse
import json
import re
from a10_admin_map import MAP_FILE
from config import PATH, VERSION
from dropbox_client import DROPBOX_ROOT, export
from helper import log_section

PAPER_DOC = f"{DROPBOX_ROOT}/Delta - wydanie online.paper"
SITE = "https://deltami.edu.pl"
LINKS_FILE = "paper-links.md"


def article_urls() -> list[tuple[str, str]]:
    path = PATH.OUTPUT / MAP_FILE
    if not path.is_file():
        raise SystemExit(f"# ERROR: brak {path} - uruchom ./main.py admin:map")
    rows = json.loads(path.read_text(encoding="utf-8"))["articles"]
    year, _, number = VERSION.partition("-")
    return [(r["title"], f"{SITE}/{year}/{number}/{r['slug']}/") for r in rows]


def build_section(urls: list[tuple[str, str]]) -> str:
    lines = [f"# {VERSION}", ""]
    for _, url in urls:
        lines += [url, ""]
    return "\n".join(lines)


@log_section
def paper_links(show_doc: bool = False) -> str:
    urls = article_urls()
    section = build_section(urls)

    PATH.OUTPUT.mkdir(parents=True, exist_ok=True)
    out = PATH.OUTPUT / LINKS_FILE
    out.write_text(section, encoding="utf-8")

    print(f"# {len(urls)} adresow, kolejnosc z druku:")
    for i, (title, url) in enumerate(urls, 1):
        print(f"#   {i:2}. {url}")
        print(f"#       {title[:66]}")
    print(f"# Zapisano fragment: {out}")

    if show_doc:
        text = export(PAPER_DOC, "markdown").decode("utf-8", "replace")
        headings = [l for l in text.splitlines() if re.match(r"#\s*\d{4}-\d{2}", l)]
        print(f"# Paper doc: {len(text):,} znakow, sekcje numerow: {', '.join(headings) or 'brak'}")
        if f"# {VERSION}" in text:
            print(f"# UWAGA: sekcja '# {VERSION}' JUZ jest w dokumencie - nie wklejaj drugi raz")
        else:
            first = headings[0] if headings else None
            where = f"nad sekcja {first}" if first else "pod tytulem dokumentu"
            print(f"# Wklej fragment {where} - najnowszy numer jest na gorze")
    return section


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--check-doc", action="store_true",
                   help="odczytaj Paper doc i sprawdz, czy sekcja numeru juz w nim jest")
    a = p.parse_args()
    paper_links(a.check_doc)
