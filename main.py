#!/usr/bin/env python3
import sys
import subprocess

from a_prepare import prepare
from b_serve import serve

ALIASES = {
    "p": "prep",
    "s": "serve",
    "n": "next",
    "d": "done",
    "r": "rsync",
}


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python main.py [{'|'.join(ALIASES.values())}] or short [{'|'.join(ALIASES.keys())}]")
        sys.exit(1)

    command = sys.argv[1]
    command = ALIASES.get(command, command)

    if command == "prep":
        prepare()
    elif command == "serve":
        serve()
    elif command == "next":
        subprocess.run(["python", "convert-2-html.py"])
    elif command == "done":
        subprocess.run(["python", "c2_move_to_done.py"])
    elif command == "rsync":
        subprocess.run(["python", "c3_sync_figures.py"])
    else:
        print(f"Nieznany parametr: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
