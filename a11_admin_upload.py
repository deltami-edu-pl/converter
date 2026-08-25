#!/usr/bin/env python3
"""
Wrzucanie artykulow do panelu admina deltami.edu.pl przez HTTPS.

ZASADY BEZPIECZENSTWA (serwis nie ma stagingu - kazdy zapis idzie na produkcje):
  * domyslnie DRY-RUN: bez --apply nic nie jest wysylane,
  * TYLKO tworzenie: POST wylacznie na /add/, nigdy na /<id>/change/,
  * artykul o istniejacym slugu w tym numerze jest POMIJANY, nie nadpisywany,
  * published pozostaje wylaczone - publikacje wlacza czlowiek w panelu,
  * formularz jest ODCZYTYWANY i odsylany z wlasnymi nadpisaniami, zeby nie
    gubic pol ukrytych i management formow inline'ow.
"""

import argparse
import json
import re
import sys
import requests
from a10_admin_map import MAP_FILE, slugify
from config import PATH
from dropbox_client import ENV_FILE, _load_env
from helper import log_section

BASE = "https://deltami.edu.pl"
# serwis odrzuca 403 zadania bez przegladarkowego User-Agenta
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
TEXT_MAX = 50000  # Article.text = CharField(max_length=50000)


class Admin:
    def __init__(self):
        env = _load_env(ENV_FILE)
        self.user = env.get("DELTA_ADMIN_USER")
        self.password = env.get("DELTA_ADMIN_PASSWORD")
        if not (self.user and self.password):
            sys.exit(f"# ERROR: brak DELTA_ADMIN_USER / DELTA_ADMIN_PASSWORD w {ENV_FILE}")
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA

    def login(self) -> None:
        self.s.get(f"{BASE}/admin/login/", timeout=30)
        token = self.s.cookies.get("csrftoken")
        r = self.s.post(f"{BASE}/admin/login/", allow_redirects=False, timeout=30,
                        headers={"Referer": f"{BASE}/admin/login/"},
                        data={"username": self.user, "password": self.password,
                              "csrfmiddlewaretoken": token, "next": "/admin/"})
        if r.status_code != 302:
            sys.exit(f"# ERROR: logowanie nieudane ({r.status_code})")
        print("# Zalogowano do panelu admina")

    def issue_articles(self, issue_id: int) -> dict[str, int]:
        """
        slug -> id dla artykulow numeru.

        Klucz to SLUG, nie tytul: tytuly roznia sie typografia miedzy zrodlem
        a recznym wpisem ("slowo…" vs "slowo. . .", "poleca:" vs "poleca -"),
        wiec dopasowanie po tytule tworzyloby duplikaty. Slug jest stabilny -
        obie wersje slugifikuja sie identycznie.
        """
        r = self.s.get(f"{BASE}/admin/journal/article/?issue__id__exact={issue_id}&all=",
                       timeout=60)
        r.raise_for_status()
        ids = re.findall(r'/admin/journal/article/(\d+)/change/', r.text)
        titles = re.findall(r'<td class="field-title">([^<]*)</td>', r.text)
        out = {}
        for art_id, title in zip(dict.fromkeys(ids), titles):
            out[slugify(title.strip())] = int(art_id)
        return out

    def max_order(self) -> int:
        """order jest globalnie narastajacy - nowy numer startuje od max+1."""
        r = self.s.get(f"{BASE}/admin/journal/article/?o=-2&all=", timeout=60)
        orders = [int(x) for x in re.findall(r'<td class="field-order">(\d+)</td>', r.text)]
        return max(orders) if orders else 0

    def add_form(self) -> dict:
        r = self.s.get(f"{BASE}/admin/journal/article/add/", timeout=60)
        r.raise_for_status()
        fields: dict[str, str] = {}
        for name, value in re.findall(
                r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', r.text):
            fields[name] = value
        for name in re.findall(r'name="([a-zA-Z0-9_\-]+)"', r.text):
            fields.setdefault(name, "")
        fields["csrfmiddlewaretoken"] = self.s.cookies.get("csrftoken") or ""
        for key in list(fields):
            if key.endswith(("TOTAL_FORMS", "INITIAL_FORMS", "MIN_NUM_FORMS", "MAX_NUM_FORMS")):
                continue
        return fields

    def create(self, payload: dict) -> bool:
        r = self.s.post(f"{BASE}/admin/journal/article/add/", data=payload,
                        headers={"Referer": f"{BASE}/admin/journal/article/add/"},
                        allow_redirects=False, timeout=120)
        if r.status_code == 302:
            return True
        errors = re.findall(r'<ul class="errorlist"[^>]*>(.*?)</ul>', r.text, re.S)[:4]
        print(f"#   ! nie utworzono ({r.status_code}): "
              + " | ".join(re.sub(r"<[^>]+>", " ", e).strip()[:90] for e in errors))
        return False


def load_map() -> list[dict]:
    path = PATH.OUTPUT / MAP_FILE
    if not path.is_file():
        sys.exit(f"# ERROR: brak {path} - uruchom ./main.py admin:map")
    return json.loads(path.read_text(encoding="utf-8"))["articles"]


@log_section
def admin_upload(issue_id: int, apply: bool = False) -> None:
    rows = load_map()
    admin = Admin()
    admin.login()

    existing = admin.issue_articles(issue_id)
    next_order = admin.max_order() + 1
    print(f"# Numer {issue_id}: {len(existing)} artykulow w panelu, nowy order od {next_order}")
    if not apply:
        print("# DRY-RUN - nic nie zostanie wyslane (--apply zeby wykonac)")

    for row in rows:
        title = row["title"]
        if row["slug"] in existing:
            print(f"# = pomijam (juz jest): {title[:60]}")
            continue
        html_path = row.get("html")
        if not html_path:
            print(f"# ! brak HTML: {title[:60]}")
            continue
        text = open(html_path, encoding="utf-8").read()
        if len(text) > TEXT_MAX:
            print(f"# ! HTML za dlugi ({len(text)} > {TEXT_MAX}): {title[:50]}")
            continue

        print(f"# + utworzenie: order={next_order} {title[:52]} "
              f"[kol={row['column'] or '-'}, dz={row['division'] or '-'}, {len(text)}B]")
        if apply:
            form = admin.add_form()
            form.update({
                "issue": str(issue_id),
                "order": str(next_order),
                "title": title,
                "slug": row["slug"],
                "text": text,
                "published": "",  # publikuje czlowiek
                "_save": "Zapisz",
            })
            if not admin.create(form):
                continue
        next_order += 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--issue", type=int, required=True, help="id numeru (journal_issue.id)")
    p.add_argument("--apply", action="store_true", help="wykonaj zapisy (domyslnie dry-run)")
    a = p.parse_args()
    admin_upload(a.issue, a.apply)
