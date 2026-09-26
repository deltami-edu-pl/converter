#!/usr/bin/env python3

import shutil
from config import PATH
from helper import log_section


@log_section
def finished():
    if not PATH.FINISHED.exists():
        print(f"# Creating folder {PATH.FINISHED}")
        PATH.FINISHED.mkdir(parents=True)
    else:
        print(f"# Folder {PATH.FINISHED} already exists")

    # DONE i OUTPUT: `done` przenosil artykuly do <numer>-done, teraz do
    # <numer>-output. Archiwizujemy oba, zeby numer w starym ukladzie tez
    # dal sie domknac.
    items = [
        PATH.DONE,
        PATH.OUTPUT,
        PATH.FIGURES,
        PATH.SOURCE,
        PATH.ROOT / "got.zip",
    ]

    for item in items:
        if not item.exists():
            print(f"# Skipped (not found): {item.name}")
            continue
        dest = PATH.FINISHED / item.name
        shutil.move(str(item), dest)
        print(f"# Moved {item.name} -> {PATH.FINISHED.name}/")

    if not PATH.ARCHIVE.exists():
        print(f"# Creating archive folder {PATH.ARCHIVE.resolve()}")
        PATH.ARCHIVE.mkdir(parents=True)
    archive_dest = PATH.ARCHIVE / PATH.FINISHED.name
    if archive_dest.exists():
        print(f"# WARNING: {archive_dest} juz istnieje, pomijam przenoszenie")
        return
    shutil.move(str(PATH.FINISHED), str(archive_dest))
    print(f"# Archived {PATH.FINISHED.name} -> {archive_dest.resolve()}")


if __name__ == "__main__":
    finished()
