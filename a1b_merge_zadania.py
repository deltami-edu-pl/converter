#!/usr/bin/env python3

from pathlib import Path
from config import PATH
from helper import log_section


def extract_zadmat_block(skip_file: Path) -> str | None:
    """
    Wyciąga blok \\def\\zadMat z pierwszego znalezionego pliku .tex (innego niż skip_file).
    Zapisuje z powrotem plik bez tego bloku i zwraca wyciętą zawartość.
    """
    for path in PATH.SOURCE.glob("*.tex"):
        if path == skip_file:
            continue

        content = path.read_text(encoding="utf-8")
        idx = content.find(r"\def\zadMat")
        if idx == -1:
            continue

        zadmat_content = content[idx:]
        path.write_text(content[:idx], encoding="utf-8")
        print(f"# Extracted \\def\\zadMat block from {path.name}")
        return zadmat_content

    return None


@log_section
def merge_zadania():
    # Find the NNNN-zadania-rozw.tex file
    zadania_rozw_pattern = "[0-9][0-9][0-9][0-9]-zadania-rozw.tex"
    zadania_rozw = next(PATH.SOURCE.glob(zadania_rozw_pattern), None)
    if not zadania_rozw:
        print(f"# ERROR: No file matching {zadania_rozw_pattern} was found.")
        return

    rozwiazania_pattern = "[0-9][0-9]-rozwiazania.tex"
    rozwiazania = next(PATH.SOURCE.glob(rozwiazania_pattern), None)
    if not rozwiazania:
        print(f"# ERROR: No file matching {rozwiazania_pattern} was found.")
        return

    rozwiazania.unlink()
    zadania_rozw.rename(rozwiazania)
    print(f"# Renamed {zadania_rozw.name} to {rozwiazania.name}")

    zadmat_content = extract_zadmat_block(rozwiazania)
    if zadmat_content is None:
        print("# ERROR: No \\def\\zadMat block found in any file.")
        return

    # Prepend the \def\zadMat block to the new zadania file
    current_text = rozwiazania.read_text(encoding="utf-8")
    rozwiazania.write_text(zadmat_content + "\n" + current_text, encoding="utf-8")
    print(f"# Prepended \\def\\zadMat block to {rozwiazania.name}")


if __name__ == "__main__":
    merge_zadania()
