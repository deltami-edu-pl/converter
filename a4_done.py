#!/usr/bin/env python3

import shutil
from config import PATH_DONE, PATH_ROOT, GET_NEXT, log_section


@log_section
def done():
    stem = GET_NEXT().stem
    print(f"# Archive files: {stem}")

    for file in list(PATH_ROOT.glob(f"{stem}*")):
        target = PATH_DONE / file.name
        shutil.move(str(file), target)
        print(f"# Moved {file.name}")


if __name__ == "__main__":
    done()
