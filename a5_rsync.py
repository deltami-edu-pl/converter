#!/usr/bin/env python3

import subprocess
from config import PATH
from helper import log_section


@log_section
def rsync():
    command = [
        "rsync",
        "-avz",
        "--progress",
        "-e",
        "ssh",
        str(PATH.FIGURES),
        "delta:/home/delta/delta-dev.mimuw.edu.pl/delta/media",
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    rsync()
