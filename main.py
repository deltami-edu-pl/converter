#!/usr/bin/env python3
import sys
import subprocess

from a_prepare import prepare
from b_serve import serve
from c_convert import convert
from d_done import done
from e_sync import sync

ALIASES = {
    "p": "prep",
    "s": "serve",
    "c": "convert",
    "d": "done",
    "r": "rsync",
}


def main():
    if len(sys.argv) < 2:
        print(
            f"Usage: python main.py [{'|'.join(ALIASES.values())}] or short [{'|'.join(ALIASES.keys())}]"
        )
        sys.exit(1)

    command = sys.argv[1]
    command = ALIASES.get(command, command)

    if command == "prep":
        prepare()
    elif command == "serve":
        serve()
    elif command == "convert":
        convert()
    elif command == "done":
        done()
    elif command == "rsync":
        sync()
    else:
        print(f"Nieznany parametr: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
