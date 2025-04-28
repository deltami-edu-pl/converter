#!/usr/bin/env python3

import subprocess
from config import VERSION


def sync_figures():
    print()
    print(f"### sync_figures")

    figures = VERSION + "-figures"

    command = [
        "rsync",
        "-avz",
        "--progress",
        "-e",
        "ssh",
        figures,
        "delta:/home/delta/delta-dev.mimuw.edu.pl/delta/media",
    ]

    try:
        subprocess.run(command, check=True)
        print(f"### sync_figures done")
        print()
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    sync_figures()
