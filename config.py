#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
import sys

COLOR = "FF0088"
NEWPAGE = "convert.html"
TEXTWIDTH = 356  # 356 pt - szerokosc strony (\textwidth) w formacie Delty; uzywane aby poprawiac szerokosc obrazkow


@dataclass
class PATH_CLASS:
    ROOT: Path
    SOURCE: Path
    FIGURES: Path
    DELTA: Path
    DONE: Path


@dataclass
class Ext:
    def __init__(self, path: Path):
        self.html = path.with_suffix(".html")
        self.tex = path.with_suffix(".tex")


@dataclass
class FILE_CLASS:
    article: Ext
    images: Ext
    source: Ext


def init_paths() -> PATH_CLASS:
    PATH_ROOT = Path(".")
    PATH_SOURCE = PATH_ROOT / "got"
    if not PATH_SOURCE.exists():
        print(f"# ERROR: Folder {PATH_SOURCE} does not exist!")
        sys.exit(1)

    VERSION = next(
        (
            p.name[:7]
            for p in PATH_SOURCE.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-delta.tex")
        ),
        None,
    )
    if not VERSION:
        print("# ERROR: VERSION is not set!")
        sys.exit(1)

    PATH_DELTA_TEX = PATH_SOURCE / (f"{VERSION}-delta.tex")
    if not PATH_DELTA_TEX.exists():
        print(f"# ERROR: File {PATH_DELTA_TEX} does not exist!")
        sys.exit(1)

    PATH_FIGURES = PATH_ROOT / f"{VERSION}-figures"
    if not PATH_FIGURES.exists():
        print(f"# Creating folder {PATH_FIGURES}")
        PATH_FIGURES.mkdir(parents=True)

    PATH_DONE = PATH_ROOT / f"{VERSION}-done"
    if not PATH_DONE.exists():
        print(f"# Creating folder {PATH_DONE}")
        PATH_DONE.mkdir(parents=True)

    print()
    print("# Paths initialized:")
    print(f"# VERSION: {VERSION}")
    print(f"# PATH_ROOT: {PATH_ROOT}")
    print(f"# PATH_SOURCE: {PATH_SOURCE}")
    print(f"# PATH_FIGURES: {PATH_FIGURES}")
    print(f"# PATH_DELTA_TEX: {PATH_DELTA_TEX}")
    print(f"# PATH_DONE: {PATH_DONE}")
    print()

    return PATH_CLASS(
        ROOT=PATH_ROOT,
        SOURCE=PATH_SOURCE,
        FIGURES=PATH_FIGURES,
        DELTA=PATH_DELTA_TEX,
        DONE=PATH_DONE,
    )


PATH = init_paths()


def FILE() -> FILE_CLASS:
    ARTICLE = "article"
    IMAGES = "images"

    first = min(
        (
            p
            for p in PATH.ROOT.iterdir()
            if p.is_file()
            and p.suffix == ".tex"
            and not p.name.endswith(f"{ARTICLE}.tex")
            and not p.name.endswith(f"{IMAGES}.tex")
        ),
        key=lambda p: p.name,
        default=None,
    )
    if first is None:
        raise FileNotFoundError(f"No base .tex file found in {PATH.ROOT}")

    stem = first.stem
    return FILE_CLASS(
        article=Ext(PATH.ROOT / f"{stem}-{ARTICLE}"),
        images=Ext(PATH.ROOT / f"{stem}-{IMAGES}"),
        source=Ext(PATH.ROOT / stem),
    )


__all__ = [
    "PATH",
    "FILE",
    "COLOR",
    "NEWPAGE",
    "TEXTWIDTH",
]
