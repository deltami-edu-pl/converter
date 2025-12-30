#!/usr/bin/env python3

import sys
from helper import log_section
from a1_prepare import prepare
from a2_convert_images import convert_images
from a3_convert_pandoc import convert_pandoc
from a4_done import done
from a5_rsync import rsync
from a6_serve import serve

ALIASES = {
    "p": "prep",
    "c": "convert",
    "ci": "convert:images",
    "cp": "convert:pandoc",
    "d": "done",
    "r": "rsync",
    "s": "serve",
}


@log_section
def main():
    if len(sys.argv) < 2:
        print_help()

    command = sys.argv[1]
    command = ALIASES.get(command, command)

    if command == "prep":
        prepare()
    elif command == "convert:images":
        convert_images()
    elif command == "convert:pandoc":
        convert_pandoc()
    elif command == "convert":
        convert_images()
        convert_pandoc()
    elif command == "done":
        done()
    elif command == "rsync":
        rsync()
    elif command == "serve":
        serve()
    else:
        print(f"Unknown command: {command}")
        print_help()
        sys.exit(1)


def print_help():
    values = "|".join(ALIASES.values())
    keys = "|".join(ALIASES.keys())
    print(f"Usage: python main.py [{values}] or short [{keys}]")
    sys.exit(1)


if __name__ == "__main__":
    main()
