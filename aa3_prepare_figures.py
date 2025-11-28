#!/usr/bin/env python3

import shutil
import subprocess
from pathlib import Path
from wand.image import Image
from config import VERSION, PATH_SOURCE, PATH_FIGURES, log_section


@log_section
def prepare_figures():
    if PATH_FIGURES.exists():
        print(f"# Directory {PATH_FIGURES} already exists")
        return

    print(f"# Creating directory {PATH_FIGURES}")
    PATH_FIGURES.mkdir(parents=True)

    # Copy images from various folders
    source_folders = ["art", "rys", "stale", "graphics"]
    pdf_files = []
    copied_files_count = 0
    converted_files_count = 0

    for source_folder in source_folders:
        source_path = PATH_SOURCE / source_folder
        if source_path.exists():
            for file in source_path.rglob("*"):
                if file.is_file():
                    suffix = file.suffix.lower()
                    if suffix in {".png", ".jpg", ".jpeg"}:
                        dest_path = PATH_FIGURES / file.name
                        shutil.copy2(file, dest_path)
                        copied_files_count += 1
                        print(f"# Copied {dest_path}")
                    elif suffix == ".pdf":
                        pdf_files.append(file)
    print(f"# Copied {copied_files_count}")
    print()

    for pdf_file in pdf_files:
        dest_path = PATH_FIGURES / (
            pdf_file.stem.replace("-eps-converted-to", "") + ".png"
        )
        try:
            with Image(filename=str(pdf_file), resolution=600) as img:
                img.format = "png"
                img.alpha_channel = "remove"
                img.background_color = "white"
                img.compression_quality = 100
                img.save(filename=str(dest_path))
            converted_files_count += 1
            print(f"# Converted {dest_path}")
        except Exception as e:
            print(f"ERROR: Converting PDF to PNG: {pdf_file.name} -> {dest_path}")
            print(f"    {e}")
    print(f"# Converted {converted_files_count}")
    print()

    files_count = copied_files_count + converted_files_count
    print(f"# Moved {files_count} files to {PATH_FIGURES}")


if __name__ == "__main__":
    prepare_figures()
