#!/usr/bin/env python3

from pathlib import Path


import shutil
from config import PATH, FILE
from helper import log_section


@log_section
def done():
    stem = FILE().source.tex.stem
    print(f"# Archive files: {stem}")

    PATH.OUTPUT.mkdir(parents=True, exist_ok=True)
    for file in list[Path](PATH.ROOT.glob(f"{stem}*")):
        target = PATH.OUTPUT / file.name
        shutil.move(str(file), target)
        print(f"# Moved {file.name}")


@log_section
def done_all():
    """
    Przenosi WSZYSTKIE gotowe artykuly do OUTPUT. release:publish potrzebuje
    tego przed archiwizacja - convert:all zostawia je w ROOT, bo nie przeklada
    plikow zeby dojsc do nastepnego artykulu.
    """
    stems = sorted(
        p.stem
        for p in PATH.ROOT.glob("[0-9][0-9]-*.tex")
        if not p.name.endswith(("-article.tex", "-images.tex"))
    )
    print(f"# Do przeniesienia: {len(stems)} artykulow")
    for stem in stems:
        for file in sorted(PATH.ROOT.glob(f"{stem}*")):
            shutil.move(str(file), PATH.OUTPUT / file.name)
        print(f"# Moved {stem}*")


if __name__ == "__main__":
    done()
