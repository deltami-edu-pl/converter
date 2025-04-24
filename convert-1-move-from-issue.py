#!/usr/bin/env python3

import os
import re
import sys
import shutil
import subprocess
from pathlib import Path
from config import VERSION, PATH_SOURCE, PATH_FIGURES, PATH_DELTA_TEX
from b1_prepare_zadania import prepare_zadania
from b2_format_tex_files import format_tex_files
from b3_prepare_figures import prepare_figures


def main():
    prepare_zadania()
    format_tex_files()
    prepare_figures()

    print()
    print(f"### convert-1-move-from-issue")
    if not VERSION:
        print("ERROR: VERSION is not set!")
        sys.exit(1)
    print(f"# Generate {VERSION} version")

    # Check if source folder exists
    if not PATH_SOURCE.exists():
        print(f"ERROR: Folder {PATH_SOURCE} does not exist!")
        sys.exit(1)
    print(f"# Source folder: ./{PATH_SOURCE}")

    # Check if delta.tex file exists
    if not PATH_DELTA_TEX.exists():
        print(f"ERROR: File {PATH_DELTA_TEX} does not exist!")
        sys.exit(1)
    print(f"# {VERSION}-delta.tex file: ./{PATH_DELTA_TEX}")

    # Find all tex files matching the pattern
    tex_files = []
    article_regex = re.compile(r"^[0-9][0-9]-.*\.tex$")
    for file in PATH_SOURCE.glob("**/*.tex"):
        if article_regex.match(file.name) and file.name != "00-spis.tex":
            tex_files.append(file)

    # Sort files
    tex_files.sort()

    # Process each tex file
    print(f"# Creating files (merging {PATH_DELTA_TEX} with 05-something.tex)")
    for tex_file in tex_files:
        filename = tex_file.name

        print(f"Creating {filename}")
        subprocess.run(
            [
                "python",
                "convert-py-1-move-from-issue.py",
                str(PATH_DELTA_TEX),
                str(tex_file),
                filename,
                str(PATH_FIGURES),
            ],
            check=True,
        )

    print("### convert-1-move-from-issue done")
    print()


if __name__ == "__main__":
    main()
