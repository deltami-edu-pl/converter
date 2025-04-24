import subprocess
from pathlib import Path
from config import PATH_SOURCE


def format_tex_files():
    print()
    print(f"### format_tex_files")

    tex_files = list(PATH_SOURCE.rglob("*.tex"))

    print(f"# Found {len(tex_files)} .tex files to format")

    for tex_file in tex_files:
        try:
            subprocess.run(
                ["latexindent", "-w", "-l", "-y=defaultSettings.yaml", str(tex_file)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"# Formatted: {tex_file}")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to format: {tex_file}")
            print(f"    {e}")

    for bak_file in PATH_SOURCE.rglob("*.bak0"):
        bak_file.unlink()

    for aux_file in PATH_SOURCE.rglob("*.aux"):
        aux_file.unlink()

    print("### format_tex_files done")
    print()


if __name__ == "__main__":
    format_tex_files()
