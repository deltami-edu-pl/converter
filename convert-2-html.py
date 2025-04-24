import sys
import subprocess
from pathlib import Path
from config import VERSION

folder = VERSION
current_dir = Path(".")

# --- Search for matching files ---
files = [
    file
    for file in current_dir.iterdir()
    if file.is_file()
    and file.suffix == ".tex"
    and not file.name.endswith("-pandoc.tex")
    and not file.name.endswith("-tikz.tex")
]

# --- Run convert command for each file ---
commands_run = []

for file in files:
    print(f"\n[ --------------- {file.name} ----------------- ]")
    print("Running: convert-py-2-html.py")

    command = ["python", "convert-py-2-html.py", f"{folder}-figures", file.name]
    print(" ".join(command))

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")

    commands_run.append(" ".join(command))

# --- Show summary ---
print("\n## FULL LIST OF CONVERT COMMANDS ##")
for cmd in commands_run:
    print(cmd)
