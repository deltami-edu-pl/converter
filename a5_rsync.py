#!/usr/bin/env python3

import subprocess
from pathlib import Path
from config import PATH
from helper import log_section


REMOTE_STATIC = "delta:/home/delta/delta-dev.mimuw.edu.pl/delta/delta/static"
STATIC_DIR = Path(__file__).parent / "static"

# klucz -> (lokalny plik, zdalny plik) dla push/pull
ASSETS = {
    "css": (str(STATIC_DIR / "article.css"), f"{REMOTE_STATIC}/css/article.css"),
    "js":  (str(STATIC_DIR / "article.js"),  f"{REMOTE_STATIC}/js/article.js"),
}


def _rsync(src: str, dst: str) -> None:
    # --chmod wymusza czytelnosc dla wszystkich uzytkownikow na zdalnej stronie,
    # niezaleznie od lokalnych uprawnien zrodla (zeby web server nie dostawal 403).
    command = [
        "rsync",
        "-avz",
        "--progress",
        "--chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r",
        "-e",
        "ssh",
        src,
        dst,
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}")


@log_section
def rsync():
    _rsync(str(PATH.FIGURES), "delta:/home/delta/delta-dev.mimuw.edu.pl/delta/media")


@log_section
def push(which: str | None = None) -> None:
    keys = [which] if which else list(ASSETS.keys())
    for k in keys:
        local, remote = ASSETS[k]
        _rsync(local, remote)


@log_section
def pull(which: str | None = None) -> None:
    keys = [which] if which else list(ASSETS.keys())
    for k in keys:
        local, remote = ASSETS[k]
        _rsync(remote, local)


if __name__ == "__main__":
    rsync()
