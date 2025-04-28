#!/usr/bin/env python3

import shutil
from config import PATH_DONE, PATH_ROOT


def move_to_done():
    print()
    print(f"### move_to_done")

    PATH_DONE.mkdir(parents=True, exist_ok=True)

    for file in PATH_ROOT.glob("*-article.html"):
        prefix = file.name.removesuffix("-article.html")
        related_files = list(PATH_ROOT.glob(f"{prefix}*"))
        print(f"# Archive files: {prefix}")

        for related_file in related_files:
            target = PATH_DONE / related_file.name
            shutil.move(str(related_file), target)
            print(f"# Moved {related_file.name}")

    print(f"### move_to_done done")
    print()


if __name__ == "__main__":
    move_to_done()
