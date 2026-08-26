#!/usr/bin/env python3

import sys
from helper import log_section
from a1_prepare import prepare
from a2_convert_images import convert_images
from a3_convert_pandoc import convert_pandoc
from a4_done import done
from a5_rsync import rsync, push, pull
from a6_serve import serve
from a7_finished import finished
from a8_review import review
from a9_checks import checks
from a10_admin_map import admin_map
from a13_dropbox_push import dropbox_push
from a14_paper_links import paper_links
from a15_release import convert_all, release_prepare, release_publish

ALIASES = {
    "p": "prep",
    "c": "convert",
    "ci": "convert:images",
    "cp": "convert:pandoc",
    "d": "done",
    "r": "rsync",
    "s": "serve",
    "f": "finish",
    "v": "review",
    "k": "checks",
    "am": "admin:map",
    "dp": "dropbox:pull",
    "dph": "dropbox:push",
    "pl": "paper:links",
    "ca": "convert:all",
    "rp": "release:prepare",
    "rpub": "release:publish",
}


@log_section
def main():
    if len(sys.argv) < 2:
        print_help()

    command = sys.argv[1]
    command = ALIASES.get(command, command)

    if command == "prep":
        prepare()
    elif command == "convert:images":
        convert_images()
    elif command == "convert:pandoc":
        convert_pandoc()
    elif command == "convert":
        convert_images()
        convert_pandoc()
    elif command == "done":
        done()
    elif command == "rsync":
        rsync()
    elif command == "push":
        push()
    elif command == "push:css":
        push("css")
    elif command == "push:js":
        push("js")
    elif command == "pull":
        pull()
    elif command == "pull:css":
        pull("css")
    elif command == "pull:js":
        pull("js")
    elif command == "serve":
        serve()
    elif command == "review":
        review()
    elif command == "checks":
        checks()
    elif command == "admin:map":
        admin_map()
    elif command == "dropbox:pull":
        # import lokalny: a12 celowo nie zalezy od config.py (got/ jeszcze nie ma)
        from a12_dropbox_pull import dropbox_pull
        dropbox_pull(None)
    elif command == "dropbox:push":
        dropbox_push()
    elif command == "paper:links":
        paper_links(show_doc=True)
    elif command == "convert:all":
        convert_all()
    elif command == "release:prepare":
        release_prepare()
    elif command == "release:publish":
        # faza publikacji dotyka produkcji - przez main.py tylko dry-run,
        # zapisy wymagaja a15_release.py publish --apply --issue <id>
        release_publish(None, apply=False)
    elif command == "finish":
        finished()
    else:
        print(f"Unknown command: {command}")
        print_help()
        sys.exit(1)


def print_help():
    values = "|".join(ALIASES.values())
    keys = "|".join(ALIASES.keys())
    print(f"Usage: python main.py [{values}] or short [{keys}]")
    sys.exit(1)


if __name__ == "__main__":
    main()
