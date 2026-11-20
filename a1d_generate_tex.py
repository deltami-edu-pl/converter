#!/usr/bin/env python3
from pathlib import Path
from config import PATH
from helper import log_section
from a1d1_wrap_with_main import wrap_with_main
from a1d2_rename_images import rename_images
from a1d3_clean_tex import clean_tex, strip_false_blocks, wrap_labeled_images
from a1d4_inline_inputs import inline_inputs, strip_comments


@log_section
def generate_tex():
    # got/stale/ trzyma artykuly z poprzednich numerow o tych samych nazwach
    # (2026-11: stary 09-iko.tex nadpisal wlasciwy) - przy duplikatach wygrywa
    # plik najplycej w drzewie
    by_name: dict[str, Path] = {}
    for file in PATH.SOURCE.glob("**/[0-9][0-9]-*.tex"):
        rel = file.relative_to(PATH.SOURCE)
        if file.name == "00-spis.tex" or "stale" in rel.parts[:-1]:
            continue
        if file.name not in by_name or len(rel.parts) < len(by_name[file.name].relative_to(PATH.SOURCE).parts):
            by_name[file.name] = file
    source_paths = sorted(by_name.values(), key=lambda f: f.name)

    for source_path in source_paths:
        print(f"# Prepare article {source_path.name}")
        content = source_path.read_text(encoding="utf-8")

        content = wrap_with_main(content)
        # strip_comments + inline_inputs MUSZA byc przed rename_images, zeby
        # \includegraphics z wklejonych fragmentow tez dostal przepisana
        # sciezke do figures/, i przed clean_tex, ktory \input-y wycina.
        content = strip_comments(content)
        content = inline_inputs(content)
        content = strip_false_blocks(content)
        content = rename_images(content)
        content = clean_tex(content)
        content = wrap_labeled_images(content)

        output_path = PATH.ROOT / source_path.name
        output_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    generate_tex()
