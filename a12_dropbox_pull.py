#!/usr/bin/env python3
"""
Pobranie dropu redakcji z Dropboxa: <ROOT>/<rok>/<NN>/got -> lokalne got.zip + got/.

NIE importuje config.py celowo: config wymaga istniejacego got/ i z niego wnioskuje
VERSION, a pull ma ten katalog dopiero utworzyc.
"""

import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
import requests
from dropbox_client import DROPBOX_ROOT, RO, access_token, api

GOT_ZIP = Path("got.zip")
GOT_DIR = Path("got")


def issue_folders() -> list[str]:
    """Wszystkie <rok>/<NN> w folderze roboczym, najnowsze na koncu."""
    out = []
    for year in sorted(e["name"] for e in api(RO, "files/list_folder",
                                             {"path": DROPBOX_ROOT})["entries"]
                       if e[".tag"] == "folder" and re.fullmatch(r"\d{4}", e["name"])):
        for entry in api(RO, "files/list_folder",
                         {"path": f"{DROPBOX_ROOT}/{year}"})["entries"]:
            if entry[".tag"] == "folder" and re.fullmatch(r"\d{2}", entry["name"]):
                out.append(f"{year}/{entry['name']}")
    return sorted(out)


def download_zip(remote: str) -> bytes:
    r = requests.post(
        "https://content.dropboxapi.com/2/files/download_zip",
        headers={"Authorization": f"Bearer {access_token(RO)}",
                 "Dropbox-API-Arg": json.dumps({"path": remote})},
        timeout=1800,
    )
    if r.status_code != 200:
        sys.exit(f"# ERROR: download_zip {remote}: {r.status_code} {r.text[:200]}")
    return r.content


def dropbox_pull(issue: str | None, force: bool = False) -> str:
    folders = issue_folders()
    if issue:
        wanted = issue.replace("-", "/")
        if wanted not in folders:
            sys.exit(f"# ERROR: brak {wanted} na Dropboksie. Dostepne: {', '.join(folders)}")
    else:
        wanted = folders[-1]
        print(f"# Najnowszy numer na Dropboksie: {wanted}")

    if GOT_DIR.exists() and not force:
        sys.exit(f"# ERROR: {GOT_DIR}/ juz istnieje - domknij numer (finish) albo uzyj --force")

    remote = f"{DROPBOX_ROOT}/{wanted}/got"
    print(f"# Pobieram {remote}")
    data = download_zip(remote)
    GOT_ZIP.write_bytes(data)
    print(f"# Zapisano {GOT_ZIP} ({len(data):,} B)")

    if GOT_DIR.exists():
        shutil.rmtree(GOT_DIR)
    with zipfile.ZipFile(GOT_ZIP) as z:
        z.extractall(".")
    tex = sorted(GOT_DIR.glob("*-delta.tex"))
    print(f"# Rozpakowano {GOT_DIR}/ ({len(list(GOT_DIR.iterdir()))} pozycji)"
          f" | glowny plik: {tex[0].name if tex else 'BRAK *-delta.tex'}")
    return wanted


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--issue", help="numer w formacie YYYY-NN (domyslnie najnowszy)")
    p.add_argument("--force", action="store_true", help="nadpisz istniejacy got/")
    a = p.parse_args()
    dropbox_pull(a.issue, a.force)
