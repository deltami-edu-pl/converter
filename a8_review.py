#!/usr/bin/env python3
"""Serwer przegladowy: lista pozycji numeru w kolejnosci z PDF + widok artykulu."""

import json
import os
import time
from pathlib import Path
from flask import Flask, abort, render_template, render_template_string, send_file, send_from_directory
from a6_serve import is_port_free, kill_stale_flask
from articles import issue_order
from config import PATH
from helper import log_section

PORT = 5000
CHECKS_FILE = "checks.json"

INDEX = """<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8">
<title>Delta {{ version }} - przeglad</title><style>
body{font:14px/1.5 -apple-system,system-ui,sans-serif;margin:2rem auto;max-width:1100px;color:#111}
h1{font-size:1.3rem;margin:0 0 .25rem}
p.sub{color:#666;margin:0 0 1.5rem}
table{border-collapse:collapse;width:100%}
th,td{text-align:left;padding:.5rem .6rem;border-bottom:1px solid #e5e5e5;vertical-align:top}
th{font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;color:#666;border-bottom:2px solid #ccc}
td.n,td.p{text-align:right;color:#888;font-variant-numeric:tabular-nums;white-space:nowrap}
a{color:#0a58ca;text-decoration:none}a:hover{text-decoration:underline}
.z{background:#fff8e1}
.ok{color:#1a7f37}.bad{color:#b42318;font-weight:600}.na{color:#aaa}
.tag{font-size:.7rem;padding:.1rem .35rem;border-radius:3px;background:#eee;color:#555;margin-left:.4rem}
</style></head><body>
<h1>Delta {{ version }}</h1>
<p class="sub">{{ articles|length }} pozycji w kolejnosci z PDF ({{ toc_name }}).
{% if not has_checks %}Checki nie byly uruchomione - <code>./main.py checks</code>.{% endif %}</p>
<table><thead><tr>
<th class="n">#</th><th class="p">str.</th><th>tytul</th><th>autor</th><th>plik</th><th>checki</th>
</tr></thead><tbody>
{% for a in articles %}
<tr{% if a.is_zadania %} class="z"{% endif %}>
<td class="n">{{ a.position }}</td>
<td class="p">{{ a.page }}</td>
<td>{% if a.html %}<a href="/a/{{ a.stem }}">{{ a.title }}</a>{% else %}{{ a.title }}{% endif %}
{% if a.is_zadania %}<span class="tag">zadania</span>{% endif %}</td>
<td>{{ a.author }}</td>
<td><code>{{ a.stem }}</code>{% if not a.html %} <span class="bad">brak HTML</span>{% endif %}</td>
<td>{% if a.stem in checks %}{% set c = checks[a.stem] %}
{% if c.failed %}<span class="bad">{{ c.failed|length }} bledow</span>{% else %}<span class="ok">OK</span>{% endif %}
{% else %}<span class="na">-</span>{% endif %}</td>
</tr>{% endfor %}
</tbody></table></body></html>"""

VIEW = """<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8">
<title>{{ a.title }}</title><style>
body{margin:0;font:14px/1.5 -apple-system,system-ui,sans-serif}
.bar{position:sticky;top:0;z-index:99;background:#111;color:#fff;padding:.5rem .9rem;display:flex;gap:1rem;align-items:center}
.bar a{color:#8ab4f8;text-decoration:none}.bar .t{font-weight:600}
.bar .err{color:#ff9d9d}
.split{display:grid;grid-template-columns:1fr 1fr;height:calc(100vh - 40px)}
.split>div{overflow:auto;border-right:1px solid #ddd}
iframe{width:100%;height:100%;border:0}
img.pdf{width:100%;display:block}
</style></head><body>
<div class="bar">
<a href="/">&larr; lista</a>
<span class="t">{{ a.position }}. {{ a.title }}</span>
<span>str. {{ a.page }} w PDF</span>
{% if failed %}<span class="err">checki: {{ failed|join(', ') }}</span>{% endif %}
<span style="margin-left:auto"><a href="/html/{{ a.stem }}" target="_blank">tylko HTML</a></span>
</div>
<div class="split">
<div><iframe src="/html/{{ a.stem }}"></iframe></div>
<div>{% for p in pages %}<img class="pdf" src="/pdf/{{ p }}" loading="lazy">{% endfor %}</div>
</div></body></html>"""


def load_checks() -> dict:
    path = PATH.OUTPUT / CHECKS_FILE
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def pdf_page_png(index: int) -> Path:
    """
    Strona PDF-a numeru jako PNG, cache w OUTPUT/pdf/. Numer strony DRUKU jest
    o 1 mniejszy od indeksu w PDF-ie (na poczatku jest okladka).
    """
    cache_dir = PATH.OUTPUT / "pdf"
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / f"p{index}.png"
    if dest.is_file():
        return dest

    pdf = next(PATH.SOURCE.glob("*-delta.pdf"), None)
    if pdf is None:
        abort(404)
    from wand.image import Image
    with Image(filename=f"{pdf}[{index}]", resolution=110) as page:
        page.format = "png"
        page.alpha_channel = "remove"
        page.background_color = "white"
        page.save(filename=str(dest))
    return dest


def build_app() -> Flask:
    app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))

    def by_stem(stem: str):
        return next((a for a in issue_order() if a.stem == stem), None)

    @app.route("/")
    def index():
        toc = next(PATH.SOURCE.glob("*-delta.toc"), None)
        return render_template_string(
            INDEX,
            version=PATH.FIGURES.name.replace("-figures", ""),
            articles=issue_order(),
            checks=load_checks(),
            has_checks=bool(load_checks()),
            toc_name=toc.name if toc else "brak .toc",
        )

    @app.route("/a/<stem>")
    def view(stem: str):
        article = by_stem(stem)
        if article is None:
            abort(404)
        checks = load_checks().get(stem, {})
        # strona druku -> indeks w PDF (+1 za okladke); pokazujemy tez nastepna,
        # bo artykul czesto przechodzi na kolejna kolumne
        first = article.page + 1
        return render_template_string(
            VIEW, a=article, pages=[first, first + 1],
            failed=[f["check"] for f in checks.get("failed", [])],
        )

    @app.route("/html/<stem>")
    def html(stem: str):
        article = by_stem(stem)
        if article is None or article.html is None:
            abort(404)
        return render_template(
            "static/template.html",
            title=article.title,
            author=article.author,
            content=article.html.read_text(encoding="utf-8"),
        )

    @app.route("/pdf/<int:index>")
    def pdf(index: int):
        return send_file(pdf_page_png(index).resolve())

    @app.route("/media/<path:filename>")
    def media(filename: str):
        if Path(filename).is_file():
            return send_from_directory(".", filename)
        abort(404)

    # template.html linkuje static/article.css WZGLEDNIE (tak jak produkcja),
    # wiec z /html/<stem> przegladarka pyta o /html/static/... . Bez CSS-a
    # layout jest inny niz na stronie i checki geometryczne nie znacza nic.
    @app.route("/static/<path:filename>")
    @app.route("/html/static/<path:filename>")
    def static_files(filename: str):
        return send_from_directory("static", filename)

    return app


@log_section
def review():
    PATH.OUTPUT.mkdir(parents=True, exist_ok=True)
    port = PORT
    if not is_port_free(port):
        kill_stale_flask(port)
    # po ubiciu poprzedniego serwera gniazdo siedzi chwile w TIME_WAIT
    for _ in range(10):
        if is_port_free(port):
            break
        time.sleep(0.5)
    if not is_port_free(port):
        print(f"# Port {port} zajety przez obcy proces - sprawdz: lsof -i :{port}")
        return
    print(f"# Przeglad numeru: http://127.0.0.1:{port}/")
    build_app().run(port=port, debug=False)


if __name__ == "__main__":
    review()
