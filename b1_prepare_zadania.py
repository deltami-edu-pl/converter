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
    zadania_rozw_path = None
    for file in PATH_SOURCE.glob("*.tex"):
        if target_pattern.match(file.name):
            zadania_rozw_path = file
            break

    if not zadania_rozw_path:
        print("ERROR: No file matching ####-zadania-rozw.tex was found.")
        return

    new_name = f"{next_number_str}-zadania-rozw.tex"
    new_path = PATH_SOURCE / new_name
    zadania_rozw_path.rename(new_path)
    print(f"# Renamed {zadania_rozw_path.name} to {new_name}")

    zadmat_content = None
    for file in PATH_SOURCE.glob("*.tex"):
        if file == new_path:
            continue  # skip the newly created file

        content = file.read_text(encoding="utf-8")
        split_index = content.find(r"\def\zadMat")

        if split_index != -1:
            # Extract the \def\zadMat block to the end
            zadmat_content = content[split_index:]
            # Save the remaining content back to the original file
            file.write_text(content[:split_index], encoding="utf-8")
            print(f"Extracted \\def\\zadMat block from {file.name}")
            break

    if zadmat_content is None:
        print("ERROR: No \\def\\zadMat block found in any file.")
        return

    # Prepend the \def\zadMat block to the new zadania file
    current_zadania_text = new_path.read_text(encoding="utf-8")
    new_path.write_text(zadmat_content + "\n" + current_zadania_text, encoding="utf-8")
    print(f"# Prepended \\def\\zadMat block to {new_name}")

    print("### prepare_zadania done")
    print()


if __name__ == "__main__":
    prepare_zadania()
