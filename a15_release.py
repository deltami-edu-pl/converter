#!/usr/bin/env python3
"""
Wydanie numeru w dwoch fazach, z bramka na przeglad po srodku.

  release:prepare   pobierz drop -> przygotuj -> przekonwertuj -> sprawdz
                    -> mapa artykulow -> otwiera sie przeglad
  <czlowiek klika i akceptuje>
  release:publish   html.zip na Dropboxa -> artykuly do panelu -> rsync figur
                    -> linki do Paper doca -> archiwizacja

Faza publikacji dotyka produkcji, wiec kazdy jej krok wymaga --apply, a bez
niego wypisuje tylko, co by zrobil.
"""

import argparse
from config import PATH, VERSION, set_target
from helper import log_section

CHECKS_FAIL_HINT = (
    "# Checki znalazly bledy - obejrzyj je w przegladzie przed publikacja"
)


def article_stems() -> list[str]:
    return sorted(
        p.stem
        for p in PATH.ROOT.glob("[0-9][0-9]-*.tex")
        if not p.name.endswith(("-article.tex", "-images.tex"))
    )


@log_section
def convert_all() -> None:
    """
    Konwertuje wszystkie artykuly, bez przekladania plikow. FILE() celuje
    kolejno w kazdy przez config.set_target - dotychczas jedyna droga do
    nastepnego artykulu bylo przeniesienie poprzedniego do innego katalogu.
    """
    from a2_convert_images import convert_images
    from a3_convert_pandoc import convert_pandoc

    stems = article_stems()
    print(f"# {len(stems)} artykulow do konwersji")
    failed: list[str] = []
    for i, stem in enumerate(stems, 1):
        print(f"\n### [{i}/{len(stems)}] {stem}")
        set_target(stem)
        try:
            convert_images()
            convert_pandoc()
        except Exception as exc:
            print(f"# ERROR {stem}: {type(exc).__name__}: {exc}")
            failed.append(stem)
    set_target(None)
    if failed:
        print(f"\n# NIE PRZESZLY: {', '.join(failed)}")
    else:
        print(f"\n# Wszystkie {len(stems)} artykulow przekonwertowane")


@log_section
def release_prepare(issue: str | None = None) -> None:
    from a1_prepare import prepare
    from a9_checks import checks
    from a10_admin_map import admin_map
    from a12_dropbox_pull import dropbox_pull

    if not PATH.SOURCE.exists() or not any(PATH.SOURCE.glob("*-delta.tex")):
        dropbox_pull(issue)
    else:
        print(f"# {PATH.SOURCE}/ juz jest - pomijam pobieranie")

    prepare()
    convert_all()
    admin_map()
    results = checks()

    errors = sum(len(v.get("failed", [])) for v in results.values())
    print()
    print(f"# Numer {VERSION}: {len(results)} artykulow, bledow w checkach: {errors}")
    if errors:
        print(CHECKS_FAIL_HINT)
    print("# Przeglad: ./main.py review  ->  http://127.0.0.1:5000/")
    print("# Po akceptacji: ./main.py release:publish --apply")


@log_section
def release_publish(issue_id: int | None = None, apply: bool = False) -> None:
    from a4_done import done_all
    from a11_admin_upload import admin_upload
    from a13_dropbox_push import dropbox_push
    from a14_paper_links import paper_links

    if not apply:
        print("# DRY-RUN calej fazy publikacji - nic nie zostanie wyslane")

    if article_stems():
        if apply:
            done_all()
        else:
            print(f"# (dry-run) przeniosloby {len(article_stems())} artykulow do {PATH.OUTPUT}")

    dropbox_push(apply)

    # upload przepisuje do mapy slugi z panelu - linki dopiero po nim
    if issue_id:
        admin_upload(issue_id, apply)
    else:
        print("# Pomijam panel admina - podaj --issue <id numeru w serwisie>")
    paper_links(show_doc=True)

    if apply:
        from a5_rsync import rsync
        rsync()
    else:
        print("# (dry-run) rsync figur na serwer")

    print()
    print("# Pozostaje recznie:")
    print(f"#   1. wklej {PATH.OUTPUT}/paper-links.md do Paper doca")
    print("#   2. wlacz 'published' na artykulach w panelu admina")
    print("#   3. ./main.py finish  - archiwizacja numeru")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["prepare", "publish"])
    p.add_argument("--issue", help="numer YYYY-NN (prepare) lub id w serwisie (publish)")
    p.add_argument("--apply", action="store_true")
    a = p.parse_args()
    if a.phase == "prepare":
        release_prepare(a.issue)
    else:
        release_publish(int(a.issue) if a.issue else None, a.apply)
