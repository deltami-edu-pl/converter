#!/usr/bin/env python3

import sys

from aa1_prepare_latex import prepare_latex
from aa2_prepare_zadania import prepare_zadania
from aa3_prepare_figures import prepare_figures
from aa4_prepare_articles import prepare_articles

from ab1_serve import serve

from ac1_convert_images import convert_images
from ac2_convert_to_html import convert_to_html
from ac4_convert_to_article import convert_to_article
from ac5_convert_zadania import convert_zadania

from ad1_done import done
from ae1_sync import sync

ALIASES = {
    "p": "prep",
    "s": "serve",
    "c": "convert",
    "d": "done",
    "r": "rsync",
}


def main():
    if len(sys.argv) < 2:
        print_help()

    command = sys.argv[1]
    command = ALIASES.get(command, command)

    print()
    print(f"### {command}")

    if command == "prep":
        prepare_latex()
        prepare_zadania()
        prepare_figures()
        prepare_articles()
    elif command == "serve":
        serve()
    elif command == "convert":
        convert_images()
        convert_to_html()
        convert_to_article()
        # convert_to_zadania()
    elif command == "done":
        done()
    elif command == "rsync":
        sync()
    else:
        print(f"Unknown command: {command}")
        print_help()
        sys.exit(1)

    print(f"### {command}")
    print()


def print_help():
    values = "|".join(ALIASES.values())
    keys = "|".join(ALIASES.keys())
    print(f"Usage: python main.py [{values}] or short [{keys}]")
    sys.exit(1)


if __name__ == "__main__":
    main()
