#!/usr/bin/env python3

import re
from pathlib import Path

PATH_ROOT = Path(".")
PATH_SOURCE = PATH_ROOT / f"got"

VERSION =  next(
    re.match(r"(\d{4}-\d{2})-delta\.tex$", f.name).group(1)
    for f in PATH_SOURCE.iterdir()
    if re.match(r"\d{4}-\d{2}-delta\.tex$", f.name)
)

PATH_DONE = PATH_ROOT / f"{VERSION}-done"
PATH_FIGURES = PATH_ROOT / f"{VERSION}-figures"
PATH_DELTA_TEX = PATH_SOURCE / (f"{VERSION}-delta.tex")

def GET_NEXT_TEX_FILE():
    files = sorted(
        [
            file
            for file in PATH_ROOT.iterdir()
            if file.is_file()
            and file.suffix == ".tex"
            and not file.name.endswith("-pandoc.tex")
            and not file.name.endswith("-tikz.tex")
        ]
    )

    return files[0] if files else None

print(f"VERSION: {VERSION}")
print(f"PATH_DONE: {PATH_DONE}")
print(f"PATH_FIGURES: {PATH_FIGURES}")
print(f"PATH_DELTA_TEX: {PATH_DELTA_TEX}")
print(f"GET_NEXT_TEX_FILE: {GET_NEXT_TEX_FILE()}")


def log_section(func):
    def wrapper(*args, **kwargs):
        name = func.__name__
        print()
        print(f"### {name}")
        result = func(*args, **kwargs)
        print()
        print(f"### {name} done")
        return result
    return wrapper
