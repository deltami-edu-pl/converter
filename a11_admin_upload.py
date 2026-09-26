#!/usr/bin/env python3
"""
Wrzucanie artykulow do panelu admina deltami.edu.pl przez HTTPS.

Admin zaklada w numerze zaslepki artykulow (tresc "x"). Skrypt tylko wstawia
HTML w miejsce "x".

ZASADY BEZPIECZENSTWA (serwis nie ma stagingu - kazdy zapis idzie na produkcje):
  * domyslnie DRY-RUN: bez --apply nic nie jest wysylane,
  * zapis TYLKO gdy obecna tresc to zaslepka ("x") - wypelniony artykul nie
    jest nadpisywany,
  * zmieniane jest wylacznie pole text; formularz jest ODCZYTYWANY i odsylany
    w calosci, zeby nie gubic pol ukrytych i management formow inline'ow,
  * published pozostaje takie, jakie ustawil admin - publikuje czlowiek,
  * niczego nie tworzymy: artykul bez zaslepki jest tylko zglaszany.
"""

import argparse
import json
import re
import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from a10_admin_map import MAP_FILE, slugify
from config import PATH
from dropbox_client import ENV_FILE, _load_env
from helper import log_section

BASE = "https://deltami.edu.pl"
# serwis odrzuca 403 zadania bez przegladarkowego User-Agenta
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
TEXT_MAX = 50000  # Article.text = CharField(max_length=50000)
PLACEHOLDER = "x"


def parse_article_form(page: str) -> dict[str, str | list[str]] | None:
    """Pola formularza tak, jak wyslalaby je przegladarka bez zadnej edycji."""
    form = BeautifulSoup(page, "html.parser").find("form", id="article_form")
    if form is None:
        return None
    fields: dict[str, str | list[str]] = {}
    for tag in form.find_all(["input", "textarea", "select"]):
        name = tag.get("name")
        if not name:
            continue
        if tag.name == "textarea":
            value = tag.get_text()
            # parser HTML przegladarki zjada jeden \n zaraz po <textarea>
            fields[name] = value[1:] if value.startswith("\n") else value
        elif tag.name == "select":
            chosen = [o.get("value", "") for o in tag.find_all("option") if o.has_attr("selected")]
            fields[name] = chosen if tag.has_attr("multiple") else (chosen[0] if chosen else "")
        elif tag.get("type") in ("checkbox", "radio"):
            if tag.has_attr("checked"):
                fields[name] = tag.get("value", "on")
        elif tag.get("type") not in ("submit", "button", "file", "image"):
            fields[name] = tag.get("value", "")
    return fields


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

    def change_form(self, article_id: int) -> dict[str, str | list[str]]:
        r = self.s.get(f"{BASE}/admin/journal/article/{article_id}/change/", timeout=60)
        r.raise_for_status()
        fields = parse_article_form(r.text)
        if fields is None:
            sys.exit(f"# ERROR: brak formularza artykulu {article_id}")
        return fields

    def update(self, article_id: int, payload: dict) -> bool:
        url = f"{BASE}/admin/journal/article/{article_id}/change/"
        r = self.s.post(url, data=payload, headers={"Referer": url},
                        allow_redirects=False, timeout=120)
        if r.status_code == 302:
            return True
        errors = re.findall(r'<ul class="errorlist"[^>]*>(.*?)</ul>', r.text, re.S)[:4]
        print(f"#   ! nie zapisano ({r.status_code}): "
              + " | ".join(re.sub(r"<[^>]+>", " ", e).strip()[:90] for e in errors))
        return False


def load_map() -> list[dict]:
    path = PATH.OUTPUT / MAP_FILE
    if not path.is_file():
        sys.exit(f"# ERROR: brak {path} - uruchom ./main.py admin:map")
    return json.loads(path.read_text(encoding="utf-8"))["articles"]


def save_map(rows: list[dict]) -> None:
    path = PATH.OUTPUT / MAP_FILE
    data = json.loads(path.read_text(encoding="utf-8"))
    data["articles"] = rows
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_issue_id(version: str) -> int | None:
    """journal_issue.id numeru YYYY-MM - rekord z data 01.MM.YYYY."""
    year, _, month = version.partition("-")
    admin = Admin()
    admin.login()
    r = admin.s.get(f"{BASE}/admin/journal/issue/?o=-1", timeout=60)
    r.raise_for_status()
    ids = list(dict.fromkeys(re.findall(r'/admin/journal/issue/(\d+)/change/', r.text)))
    for issue_id in ids[:6]:
        page = admin.s.get(f"{BASE}/admin/journal/issue/{issue_id}/change/", timeout=60).text
        if re.search(rf'name="date"[^>]*value="01\.{month}\.{year}"', page):
            return int(issue_id)
    return None


def match_article(slug: str, existing: dict[str, int]) -> int | None:
    """Slug z mapy albo slug zaslepki bedacy jego koncowka (admin skraca tytul)."""
    if slug in existing:
        return existing[slug]
    hits = [i for s, i in existing.items() if slug.endswith(s) or s.endswith(slug)]
    return hits[0] if len(hits) == 1 else None


@log_section
def admin_upload(issue_id: int, apply: bool = False) -> None:
    rows = load_map()
    admin = Admin()
    admin.login()

    existing = admin.issue_articles(issue_id)
    print(f"# Numer {issue_id}: {len(existing)} zaslepek/artykulow w panelu")
    if not apply:
        print("# DRY-RUN - nic nie zostanie wyslane (--apply zeby wykonac)")

    used: set[int] = set()
    slugs_by_id = {i: s for s, i in existing.items()}
    for row in rows:
        title = row["title"]
        article_id = match_article(row["slug"], existing)
        if article_id is None:
            print(f"# ! brak zaslepki w panelu: {title[:60]}")
            continue
        used.add(article_id)
        if row["slug"] != slugs_by_id[article_id]:
            print(f"# ~ slug z panelu: {row['slug']} -> {slugs_by_id[article_id]}")
            row["slug"] = slugs_by_id[article_id]
        html_path = row.get("html")
        if not html_path:
            print(f"# ! brak HTML: {title[:60]}")
            continue
        path = Path(html_path)
        if not path.is_file():
            path = PATH.OUTPUT / path.name
        text = path.read_text(encoding="utf-8")
        if len(text) > TEXT_MAX:
            print(f"# ! HTML za dlugi ({len(text)} > {TEXT_MAX}): {title[:50]}")
            continue

        form = admin.change_form(article_id)
        current = str(form.get("text", "")).strip()
        if current != PLACEHOLDER:
            print(f"# = pomijam (tresc to nie zaslepka, {len(current)}B): [{article_id}] {title[:50]}")
            continue

        print(f"# + wstawiam HTML: [{article_id}] {title[:52]} ({len(text)}B)")
        if apply:
            before = dict(form)
            payload = {**form, "text": text, "_save": "Zapisz"}
            if admin.update(article_id, payload):
                after = admin.change_form(article_id)
                if str(after.get("text", "")).strip() != text.strip():
                    print(f"#   ! po zapisie tresc sie rozni ({len(str(after.get('text', '')))}B)")
                changed = sorted(
                    k for k in set(before) | set(after)
                    if k not in ("text", "csrfmiddlewaretoken") and before.get(k) != after.get(k)
                )
                if changed:
                    print(f"#   ! zmienily sie inne pola niz text: {', '.join(changed)}")

    save_map(rows)

    for slug, article_id in existing.items():
        if article_id not in used:
            print(f"# ? zaslepka bez artykulu w mapie: [{article_id}] {slug}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--issue", type=int, required=True, help="id numeru (journal_issue.id)")
    p.add_argument("--apply", action="store_true", help="wykonaj zapisy (domyslnie dry-run)")
    a = p.parse_args()
    admin_upload(a.issue, a.apply)
