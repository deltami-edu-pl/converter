#!/usr/bin/env python3

from config import FILE
from helper import log_section

from a3a0_clean_tex import clean_tex
from a3a0b_clean_rozwiazania import clean_rozwiazania
from a3a1_prepare_tex import prepare_tex
from a3a2_replace_algorithms import replace_algorithms
from a3a2b_crop_trim_images import crop_trim_images
from a3a3_replace_images import replace_images
from a3a4_fix_bibliography import fix_bibliography
from a3a5_expand_rys_captions import expand_rys_captions
from a3a6_auto_number_equations import auto_number_equations


@log_section
def prepare_pandoc():
    content = FILE().source.tex.read_text(encoding="utf-8")

    if "rozwiazania" in FILE().source.tex.name:
        content = clean_rozwiazania(content)
    content = clean_tex(content)
    content = prepare_tex(content)
    content = replace_algorithms(content)
    content = crop_trim_images(content)
    content = replace_images(content)
    content = fix_bibliography(content)
    content = expand_rys_captions(content)
    content = auto_number_equations(content)

    return content


if __name__ == "__main__":
    prepare_pandoc()
