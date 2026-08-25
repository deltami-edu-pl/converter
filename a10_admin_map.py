#!/usr/bin/env python3
"""Mapa pozycji numeru -> rekordy artykulow w panelu admina."""

import json
import re
from admin_rules import (COLUMN_BY_MACRO, COLUMN_BY_TITLE_PREFIX, FIXED_TITLE,
                         PL, TITLE_PREFIX)
from articles import ARTICLE_MACROS, issue_order, toc_entries
from config import PATH
from helper import log_section

MAP_FILE = "admin-map.json"


def slugify(title: str) -> str:
    """Jak django.utils.text.slugify, ale z transliteracja polskich znakow."""
    s = title.translate(PL).lower()
    s = s.replace("„", "").replace("”", "").replace("’", "")
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s


def normalize_quotes(text: str) -> str:
    """,,X'' -> „X” - konwencja serwisu, zob. tytuly wpisane recznie w 2026-09."""
    return re.sub(r",,\s*", "\u201e", text).replace("''", "\u201d")


def admin_title(macro: str, title: str, subtitle: str) -> str:
    title = normalize_quotes(title)
    subtitle = normalize_quotes(subtitle or "")
    if macro in FIXED_TITLE:
        return FIXED_TITLE[macro]
    prefix = TITLE_PREFIX.get(macro)
    if prefix:
        rest = subtitle or title
        if rest and rest != prefix:
            return f"{prefix}: {rest}"
        return prefix
    return title


def column_for(macro: str, title: str) -> str:
    column = COLUMN_BY_MACRO.get(macro, "")
    if column:
        return column
    for prefix, slug in COLUMN_BY_TITLE_PREFIX.items():
        if title.startswith(prefix):
            return slug
    return ""


@log_section
def admin_map() -> dict:
    entries = [e for e in toc_entries() if e[0] in ARTICLE_MACROS]
    macros = {}
    for (macro, title, author, page, subtitle), art in zip(entries, issue_order()):
        macros[art.stem] = (macro, title, subtitle)

    rows = []
    for art in issue_order():
        macro, toc_title, subtitle = macros.get(art.stem, ("poz", art.title, ""))
        title = admin_title(macro, toc_title or art.title, subtitle)
        rows.append({
            "stem": art.stem,
            "position": art.position,
            "macro": macro,
            "title": title,
            "slug": slugify(title),
            "column": column_for(macro, title),
            "division": "",
            "author": art.author,
            "html": str(art.html) if art.html else None,
        })

    PATH.OUTPUT.mkdir(parents=True, exist_ok=True)
    out = PATH.OUTPUT / MAP_FILE
    out.write_text(json.dumps({"articles": rows}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"# Zapisano {out} ({len(rows)} pozycji)")
    return {"articles": rows}


if __name__ == "__main__":
    admin_map()
