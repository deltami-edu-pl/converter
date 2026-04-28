#!/usr/bin/env python3

import shutil
from config import PATH, VERSION
from helper import log_section


@log_section
def finished():
    target = PATH.ROOT / f"{VERSION}-finished"
    if not target.exists():
        print(f"# Creating folder {target}")
        target.mkdir(parents=True)
    else:
        print(f"# Folder {target} already exists")

    items = [
        PATH.DONE,
        PATH.FIGURES,
        PATH.SOURCE,
        PATH.ROOT / "got.zip",
    ]

    for item in items:
        if not item.exists():
            print(f"# Skipped (not found): {item.name}")
            continue
        dest = target / item.name
        shutil.move(str(item), dest)
        print(f"# Moved {item.name} -> {target.name}/")


if __name__ == "__main__":
    finished()
