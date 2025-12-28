#!/usr/bin/env python3

import unicodedata
import re
import os
import requests
import urllib.error
import sys
import urllib.parse
from bs4 import BeautifulSoup
from bs4 import Comment
from urllib.parse import urljoin, urlparse
from urllib.request import urlretrieve
import subprocess
from config import (
    VERSION,
    GET_NEXT,
    log_section,
    COLOR,
    IMAGES,
    PANDOC,
    PATH_FIGURES,
    PATH_ROOT,
    contain_tikz,
)
from a3a1_prepare_tex import prepare_tex
from a3a2_replace_algorithms import replace_algorithms

from a3a3_replace_images import replace_images
from a3a4_fix_bibliography import fix_bibliography
from a3a5_expand_rys_captions import expand_rys_captions
from a3a6_auto_number_equations import auto_number_equations


@log_section
def prepare_pandoc():
    content = GET_NEXT().read_text(encoding="utf-8")

    content = prepare_tex(content)
    content = replace_algorithms(content)
    content = replace_images(content)
    content = fix_bibliography(content)
    content = expand_rys_captions(content)
    content = auto_number_equations(content)

    return content


if __name__ == "__main__":
    prepare_pandoc()
