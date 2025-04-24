#!/usr/bin/env python3

import os
import re
import sys
import shutil
import subprocess
from pathlib import Path
from config import VERSION


def main():
    folder = VERSION
    if not VERSION:
        print("ERROR: VERSION is not set!")
        sys.exit(1)
    print(f"# Generate {VERSION} version")

    # Check if source folder exists
    folder_path = Path(folder)
    if not folder_path.exists():
        print(f"ERROR: Folder {folder} does not exist!")
        sys.exit(1)
    print(f"# Source folder: ./{folder_path}")

    # Create figures directory if it doesn't exist
    figures_folder = Path(f"{folder}-figures")
    if not figures_folder.exists():
        print(f"# Creating directory {folder}-figures")
        figures_folder.mkdir(parents=True)
    print(f"# Figures folder: ./{figures_folder}")

    # Check if delta.tex file exists
    delta_tex = folder_path / f"{folder}-delta.tex"
    if not delta_tex.exists():
        print(f"ERROR: File {folder}/{folder}-delta.tex does not exist!")
        sys.exit(1)
    print(f"# Delta.tex file: ./{delta_tex}")

    # Copy images from various folders
    source_folders = ["art", "ilustracje", "rys", "stale"]
    allowed_extensions = {".png", ".pdf", ".jpg", ".jpeg"}
    copied_files_count = 0

    for source_folder in source_folders:
        source_path = folder_path / source_folder
        if source_path.exists():
            for file in source_path.rglob("*"):
                if file.is_file() and file.suffix.lower() in allowed_extensions:
                    shutil.copy2(file, figures_folder)
                    copied_files_count += 1

    print(f"# Copied {copied_files_count} files to ./{figures_folder}")

    # Count PDF files and convert them to PNG
    pdf_files = list(figures_folder.glob("*.pdf"))
    filecount = len(pdf_files)
    print(f"# Converting pdf files to png (number of files: {filecount})")

    # Run the PDF to PNG conversion script
    subprocess.run(["bash", "convert-py-0-pdf2png.sh", str(figures_folder)], check=True)

    # Find all tex files matching the pattern
    tex_files = []
    article_regex = re.compile(r"^[0-9][0-9]-.*\.tex$")
    for file in folder_path.glob("**/*.tex"):
        if article_regex.match(file.name) and file.name != "00-spis.tex":
            tex_files.append(file)

    # Sort files
    tex_files.sort()

    # Process each tex file
    print(f"# Creating files (merging {folder}-delta.tex with 05-something.tex)")
    for tex_file in tex_files:
        filename = tex_file.name

        print(f"Creating {filename}")
        subprocess.run(
            [
                "python",
                "convert-py-1-move-from-issue.py",
                str(delta_tex),
                str(tex_file),
                filename,
                str(figures_folder),
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
