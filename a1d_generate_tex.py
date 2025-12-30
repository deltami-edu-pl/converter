#!/usr/bin/env python3
from config import PATH
from helper import log_section
from a1d1_wrap_with_main import wrap_with_main
from a1d2_rename_images import rename_images
from a1d3_clean_tex import clean_tex


@log_section
def generate_tex():
    source_paths = sorted(
        file
        for file in PATH.SOURCE.glob("**/[0-9][0-9]-*.tex")
        if file.name != "00-spis.tex"
    )

    for source_path in source_paths:
        print(f"# Prepare article {source_path.name}")
        content = source_path.read_text(encoding="utf-8")

        content = wrap_with_main(content)
        content = rename_images(content)
        content = clean_tex(content)

        output_path = PATH.ROOT / source_path.name
        output_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    generate_tex()
