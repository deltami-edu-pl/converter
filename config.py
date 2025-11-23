from pathlib import Path

VERSION = "2025-12"

PATH_ROOT = Path(".")
PATH_SOURCE = PATH_ROOT / VERSION
PATH_DONE = PATH_ROOT / (f"{VERSION}-done")
PATH_FIGURES = PATH_ROOT / (f"{VERSION}-figures")
PATH_DELTA_TEX = PATH_SOURCE / (f"{VERSION}-delta.tex")
