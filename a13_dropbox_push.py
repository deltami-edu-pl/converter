#!/usr/bin/env python3
"""
Spakowanie gotowych artykulow do html.zip i wrzucenie na Dropboxa.

Struktura archiwum jest zgodna z ta, ktora redakcja trzyma dotychczas:
katalog html/ z plikami <NN>-<slug>-article.html w korzeniu archiwum.
Domyslnie DRY-RUN - bez --apply nic nie leci na Dropboxa.
"""

import argparse
import io
import zipfile
from pathlib import Path
from config import PATH, VERSION
from dropbox_client import DROPBOX_ROOT, RO, DropboxError, api, enable_writes, upload
from helper import log_section

ARCHIVE_DIR = "html"
ARCHIVE_NAME = "html.zip"


def article_html() -> list[Path]:
    """
    Gotowe artykuly. Szukamy w OUTPUT, potem DONE, potem ROOT - artykul
    wedruje miedzy nimi w trakcie numeru, a do archiwum chcemy jedna
    kopie kazdego (pierwsze znalezione wygrywa).
    """
    found: dict[str, Path] = {}
    for folder in (PATH.OUTPUT, PATH.DONE, PATH.ROOT):
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*-article.html")):
            found.setdefault(path.name, path)
    return [found[name] for name in sorted(found)]


def build_zip(files: list[Path]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{ARCHIVE_DIR}/", "")
        for path in files:
            z.write(path, f"{ARCHIVE_DIR}/{path.name}")
    return buffer.getvalue()


def remote_path() -> str:
    year, _, number = VERSION.partition("-")
    return f"{DROPBOX_ROOT}/{year}/{number}/{ARCHIVE_NAME}"


@log_section
def dropbox_push(apply: bool = False) -> None:
    files = article_html()
    if not files:
        print("# ERROR: nie znalazlem zadnego *-article.html")
        return

    data = build_zip(files)
    remote = remote_path()
    print(f"# {len(files)} artykulow -> {ARCHIVE_NAME} ({len(data):,} B)")
    for path in files:
        print(f"#   {path.stat().st_size:>8,} B  {ARCHIVE_DIR}/{path.name}")

    try:
        existing = api(RO, "files/get_metadata", {"path": remote})
        print(f"# Na Dropboksie JUZ JEST: {existing.get('size', 0):,} B, "
              f"{existing.get('client_modified', '')[:10]} - zostanie nadpisany")
    except DropboxError:
        print("# Na Dropboksie jeszcze nie ma tego pliku")

    print(f"# Cel: {remote}")
    if not apply:
        print("# DRY-RUN - nic nie wyslano (--apply zeby wykonac)")
        return

    enable_writes(f"html.zip numeru {VERSION}")
    result = upload(remote, data, overwrite=True)
    print(f"# Wyslano: {result.get('path_display')} ({result.get('size', 0):,} B)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true", help="wykonaj upload (domyslnie dry-run)")
    a = p.parse_args()
    dropbox_push(a.apply)
