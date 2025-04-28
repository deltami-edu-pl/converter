#!/usr/bin/env python3
import sys
import subprocess


def main():
    if len(sys.argv) < 2:
        print("Użycie: python main.py [done|next]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "next":
        subprocess.run(["python", "convert-2-html.py"])
    elif command == "done":
        subprocess.run(["python", "c2_move_to_done.py"])
    elif command == "sync":
        subprocess.run(["python", "c3_sync_figures.py"])
    else:
        print(f"Nieznany parametr: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
