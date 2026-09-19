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


if __name__ == "__main__":
    done()
