#!/usr/bin/env python3

import re
from pathlib import Path
from wand.image import Image
import sys

COLOR = "FF0088"
NEWPAGE = "convert.html"
TEXTWIDTH = 356  # 356 pt - szerokosc strony (\textwidth) w formacie Delty; uzywane aby poprawiac szerokosc obrazkow
IMAGES = "images"
PANDOC = "pandoc"

PATH_ROOT = Path(".")
PATH_SOURCE = PATH_ROOT / f"got"

if not PATH_SOURCE.exists():
    print(f"ERROR: Folder {PATH_SOURCE} does not exist!")
    sys.exit(1)


def first_match(pattern: str) -> Path | None:
    """Zwraca pierwszy plik pasujący do glob pattern albo None."""
    return next(PATH_SOURCE.glob(pattern), None)


VERSION = first_match("[0-9][0-9][0-9][0-9]-[0-9][0-9]-delta.tex").name[:7]

if not VERSION:
    print("ERROR: VERSION is not set!")
    sys.exit(1)

PATH_DELTA_TEX = PATH_SOURCE / (f"{VERSION}-delta.tex")
if not PATH_DELTA_TEX.exists():
    print(f"ERROR: File {PATH_DELTA_TEX} does not exist!")
    sys.exit(1)

PATH_FIGURES = PATH_ROOT / f"{VERSION}-figures"
if not PATH_FIGURES.exists():
    print(f"# Creating folder {PATH_FIGURES}")
    PATH_FIGURES.mkdir(parents=True)

PATH_DONE = PATH_ROOT / f"{VERSION}-done"
if not PATH_DONE.exists():
    print(f"# Creating folder {PATH_DONE}")
    PATH_DONE.mkdir(parents=True)


def GET_NEXT():
    files = sorted(
        [
            file
            for file in PATH_ROOT.iterdir()
            if file.is_file()
            and file.suffix == ".tex"
            and not file.name.endswith(PANDOC + ".tex")
            and not file.name.endswith(IMAGES + ".tex")
        ]
    )

    return files[0] if files else None


print(f"VERSION: {VERSION}")
print(f"PATH_ROOT: {PATH_ROOT}")
print(f"PATH_SOURCE: {PATH_SOURCE}")
print(f"PATH_FIGURES: {PATH_FIGURES}")
print(f"PATH_DELTA_TEX: {PATH_DELTA_TEX}")
print(f"PATH_DONE: {PATH_DONE}")
print(f"GET_NEXT: {GET_NEXT()}")
print()
print()


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


def contain_tikz(content: str) -> bool:
    return len(re.findall(r"\\begin\{tikzpicture\}", content)) > 0


def convert_pdf_to_png(pdf_file: Path, dest_path: Path) -> bool:
    try:
        with Image(filename=str(pdf_file), resolution=600) as img:
            img.format = "png"
            img.alpha_channel = "remove"
            img.background_color = "white"
            img.compression_quality = 100
            img.save(filename=str(dest_path))
        return True
    except Exception as e:
        print(f"# ERROR: Converting PDF to PNG: {pdf_file.name} -> {dest_path}")
        print(f"    {e}")
        return False
