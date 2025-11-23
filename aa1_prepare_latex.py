#!/usr/bin/env python3
import subprocess
from pathlib import Path
from config import PATH_SOURCE, log_section


@log_section
def prepare_latex():
    latexindent_args = ["latexindent", "-w", "-l", "-y=defaultSettings.yaml"]

    if not Path("defaultSettings.yaml").exists():
        raise FileNotFoundError("Brakuje pliku defaultSettings.yaml")

    tex_files = sorted(PATH_SOURCE.rglob("*.tex"))
    print(f"# Found {len(tex_files)} .tex files to format")

    for tex_file in tex_files:
        try:
            subprocess.run(
                latexindent_args + [str(tex_file)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"# Formatted: {tex_file}")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to format: {tex_file}")
            print(f"    {e}")

    # Cleanup backup and aux files
    for ext in ["*.bak0", "*.aux"]:
        for file in PATH_SOURCE.rglob(ext):
            file.unlink()

if __name__ == "__main__":
    prepare_latex()
