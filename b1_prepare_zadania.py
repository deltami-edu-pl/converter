import re
from pathlib import Path
from config import PATH_SOURCE


def prepare_zadania():
    print()
    print(f"### prepare_zadania")

    existing_numbers = []
    pattern_existing = re.compile(r"^(\d{2})-.*\.tex$")
    for file in PATH_SOURCE.glob("*.tex"):
        match = pattern_existing.match(file.name)
        if match:
            existing_numbers.append(int(match.group(1)))

    next_number = max(existing_numbers, default=0) + 1
    next_number_str = f"{next_number:02}"

    target_pattern = re.compile(r"^\d{4}-zadania-rozw\.tex$")
    for file in PATH_SOURCE.glob("*.tex"):
        if target_pattern.match(file.name):
            new_name = f"{next_number_str}-zadania.tex"
            file.rename(PATH_SOURCE / new_name)
            print(f"# Renamed {file.name} → {new_name}")
            print("### prepare_zadania done")
            print()
            return

    print("ERROR: Cannot find file in format ####-zadania-rozw.tex")


if __name__ == "__main__":
    prepare_zadania()
