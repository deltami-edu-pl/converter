#!/usr/bin/env python3

from c1_convert_to_html import convert_to_html
from c4_convert_to_article import convert_to_article


def convert():
    print()
    print(f"### convert")

    convert_to_html()
    convert_to_article()

    print("### convert done")
    print()


if __name__ == "__main__":
    convert()
