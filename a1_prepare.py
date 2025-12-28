#!/usr/bin/env python3

from a1a_intent_tex import intent_tex
from a1b_merge_zadania import merge_zadania
from a1c_prepare_images import prepare_images
from a1d_generate_tex import generate_tex


def prepare():
    intent_tex()
    merge_zadania()
    prepare_images()
    generate_tex()
