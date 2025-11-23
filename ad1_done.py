#!/usr/bin/env python3

import shutil
from config import PATH_DONE, PATH_ROOT, GET_NEXT_TEX_FILE, log_section

@log_section
def done():

    PATH_DONE.mkdir(parents=True, exist_ok=True)

    filename = GET_NEXT_TEX_FILE()
    print(f"# Archive files: {filename}")

    prefix = filename.stem
    related_files = list(PATH_ROOT.glob(f"{prefix}*"))
    for related_file in related_files:
        target = PATH_DONE / related_file.name
        shutil.move(str(related_file), target)
        print(f"# Moved {related_file.name}")

if __name__ == "__main__":
    done()
