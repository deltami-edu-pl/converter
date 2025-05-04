#!/usr/bin/env python3

from a1_prepare_zadania import prepare_zadania
from a2_prepare_latex import prepare_latex
from a3_prepare_figures import prepare_figures
from a4_prepare_articles import prepare_articles


def prepare():
    prepare_zadania()
    prepare_latex()
    prepare_figures()
    prepare_articles()


if __name__ == "__main__":
    prepare()
