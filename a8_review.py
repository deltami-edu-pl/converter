#!/usr/bin/env python3
"""Serwer przegladowy: lista pozycji numeru, widok artykulu z uwagami, przyciski wydania."""

import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from flask import (Flask, abort, jsonify, render_template, render_template_string, request,
                   send_file, send_from_directory)
from a6_serve import is_port_free, kill_stale_flask
from articles import issue_order
from config import PATH
from helper import log_section

PORT = 5000
CHECKS_FILE = "checks.json"
COMMENTS_FILE = "review-comments.json"
LINKS_FILE = "paper-links.md"

ACTIONS = {
    "publish-dry": {
        "label": "Podgląd publikacji (dry-run)",
        "needs_issue": True,
        "confirm": "",
        "argv": lambda issue: ["a15_release.py", "publish", "--issue", str(issue)],
        "info": "Pokazuje, co zrobiłaby publikacja: które zaślepki w panelu dostaną HTML, "
                "co pójdzie na Dropbox i na serwer. Niczego nie wysyła ani nie przenosi.",
    },
    "publish": {
        "label": "Publikuj",
        "needs_issue": True,
        "confirm": "Publikacja na produkcję: Dropbox, panel admina (tylko treść zaślepek \"x\") i rsync figur. Kontynuować?",
        "argv": lambda issue: ["a15_release.py", "publish", "--issue", str(issue), "--apply"],
        "info": "Przenosi pliki numeru do katalogu output, wysyła html.zip na Dropbox, "
                "wstawia HTML w miejsce \"x\" w zaślepkach artykułów w panelu (nic poza treścią, "
                "published bez zmian), generuje linki do Paper doca i robi rsync figur na serwer.",
    },
    "finish": {
        "label": "Zakończ numer",
        "needs_issue": False,
        "confirm": "Archiwizacja numeru do ../!DONE/. Po tym portal będzie pusty. Kontynuować?",
        "argv": lambda issue: ["main.py", "finish"],
        "info": "Archiwizuje cały numer (output, figury, got/, uwagi z przeglądu) do ../!DONE/. "
                "Na sam koniec: po wklejeniu linków do Paper doca i włączeniu published w panelu.",
    },
}

JOB = {"action": None, "running": False, "lines": [], "code": None, "started": None}
JOB_LOCK = threading.Lock()
COMMENTS_LOCK = threading.Lock()

INDEX = r"""<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8">
<title>Delta {{ version }} - przeglad</title><style>
body{font:14px/1.5 -apple-system,system-ui,sans-serif;margin:2rem auto;max-width:1100px;color:#111;padding:0 1rem}
h1{font-size:1.3rem;margin:0 0 .25rem}
h2{font-size:1rem;margin:2rem 0 .6rem}
p.sub{color:#666;margin:0 0 1.5rem}
table{border-collapse:collapse;width:100%}
th,td{text-align:left;padding:.5rem .6rem;border-bottom:1px solid #e5e5e5;vertical-align:top}
th{font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;color:#666;border-bottom:2px solid #ccc}
td.n,td.p{text-align:right;color:#888;font-variant-numeric:tabular-nums;white-space:nowrap}
a{color:#0a58ca;text-decoration:none}a:hover{text-decoration:underline}
.z{background:#fff8e1}
.ok{color:#1a7f37}.bad{color:#b42318;font-weight:600}.na{color:#aaa}
.tag{font-size:.7rem;padding:.1rem .35rem;border-radius:3px;background:#eee;color:#555;margin-left:.4rem}
.cnt{display:inline-block;min-width:1.4rem;text-align:center;border-radius:9px;background:#fde68a;color:#7c2d12;font-weight:600;font-size:.75rem;padding:0 .35rem}
.actions{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:.8rem}
.card{border:1px solid #ddd;border-radius:8px;padding:.8rem 1rem}
.card p{margin:.4rem 0 0;color:#555;font-size:13px}
button{font:inherit;padding:.35rem .8rem;border-radius:6px;border:1px solid #bbb;background:#f6f6f6;cursor:pointer}
button.danger{background:#b42318;color:#fff;border-color:#b42318}
button:disabled{opacity:.5;cursor:default}
.issue{margin:.2rem 0 .8rem}
.issue input{font:inherit;width:6rem;padding:.25rem .4rem}
pre#log{background:#111;color:#ddd;padding:.8rem;border-radius:8px;max-height:420px;overflow:auto;font-size:12px;white-space:pre-wrap;display:none}
textarea.links{width:100%;height:9rem;font:12px ui-monospace,monospace}
</style></head><body>
<h1>Delta {{ version }}</h1>
<p class="sub">{{ articles|length }} pozycji w kolejnosci z PDF ({{ toc_name }}).
{% if not has_checks %}Checki nie byly uruchomione - <code>./main.py checks</code>.{% endif %}
Klik w tytul otwiera artykul w nowej karcie - tam zaznacz tekst (albo Alt+klik na obrazek), zeby dodac uwage.
<a href="/uwagi">Wszystkie uwagi ({{ open_total }} otwartych)</a></p>
<table><thead><tr>
<th class="n">#</th><th class="p">str.</th><th>tytul</th><th>autor</th><th>plik</th><th>checki</th><th>uwagi</th>
</tr></thead><tbody>
{% for a in articles %}
<tr{% if a.is_zadania %} class="z"{% endif %}>
<td class="n">{{ a.position }}</td>
<td class="p">{{ a.page }}</td>
<td>{% if a.html %}<a href="/html/{{ a.stem }}" target="_blank">{{ a.title }}</a>{% else %}{{ a.title }}{% endif %}
{% if a.is_zadania %}<span class="tag">zadania</span>{% endif %}
<a href="/a/{{ a.stem }}" class="tag" title="HTML obok PDF-a">vs PDF</a></td>
<td>{{ a.author }}</td>
<td><code>{{ a.stem }}</code>{% if not a.html %} <span class="bad">brak HTML</span>{% endif %}</td>
<td>{% if a.stem in checks %}{% set c = checks[a.stem] %}
{% if c.failed %}<span class="bad">{{ c.failed|length }} bledow</span>{% else %}<span class="ok">OK</span>{% endif %}
{% else %}<span class="na">-</span>{% endif %}</td>
<td>{% if open_counts.get(a.stem) %}<a href="/uwagi#{{ a.stem }}"><span class="cnt">{{ open_counts[a.stem] }}</span></a>{% else %}<span class="na">-</span>{% endif %}</td>
</tr>{% endfor %}
</tbody></table>

<h2>Wydanie</h2>
<div class="issue"><label>ID numeru w panelu admina (<code>journal_issue.id</code>):
<input id="issue" placeholder="..."></label> <button id="detect">wykryj</button> <span id="issue-info" class="na"></span></div>
<div class="actions">
{% for key, act in actions.items() %}
<div class="card"><button data-action="{{ key }}" data-confirm="{{ act.confirm }}" data-issue="{{ 1 if act.needs_issue else 0 }}"
{% if key != 'publish-dry' %}class="danger"{% endif %}>{{ act.label }}</button>
<p>{{ act.info }}</p></div>
{% endfor %}
</div>
<pre id="log"></pre>
{% if links %}<h2>Linki do Paper doca</h2>
<p class="sub">Wklej nad najnowsza sekcje w Paper docu.</p>
<textarea class="links" readonly>{{ links }}</textarea><br><button id="copy-links">Kopiuj</button>{% endif %}

<script>
const $ = s => document.querySelector(s);
const issue = $("#issue"), log = $("#log"), info = $("#issue-info");
async function detect(){
  info.textContent = "szukam w panelu...";
  try{
    const r = await (await fetch("/api/issue-id")).json();
    if(r.id){ issue.value = r.id; info.textContent = "numer " + r.version + " (data 01." + r.version.split("-")[1] + ")"; }
    else info.textContent = r.error || "nie znaleziono";
  }catch(e){ info.textContent = "blad: " + e; }
}
$("#detect").onclick = detect;
detect();
let timer = null;
function setBusy(b){ document.querySelectorAll("button[data-action]").forEach(x => x.disabled = b); }
async function poll(){
  const j = await (await fetch("/api/job")).json();
  if(!j.action) return;
  log.style.display = "block";
  log.textContent = j.lines.join("\n") + (j.running ? "\n..." : "\n\n# koniec, kod wyjscia: " + j.code);
  log.scrollTop = log.scrollHeight;
  setBusy(j.running);
  if(j.running){ timer = setTimeout(poll, 1000); } else if(timer !== null){ timer = null; }
}
document.querySelectorAll("button[data-action]").forEach(b => b.onclick = async () => {
  if(b.dataset.issue === "1" && !/^\d+$/.test(issue.value)){ alert("Podaj ID numeru"); return; }
  if(b.dataset.confirm && !confirm(b.dataset.confirm)) return;
  const r = await fetch("/api/run/" + b.dataset.action, {method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({issue: issue.value})});
  const j = await r.json();
  if(!r.ok){ alert(j.error); return; }
  poll();
});
poll();
const cl = $("#copy-links");
if(cl) cl.onclick = () => { navigator.clipboard.writeText($("textarea.links").value); cl.textContent = "Skopiowano"; };
</script>
</body></html>"""

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


OVERLAY = """
<style>
::highlight(review-note){background:#fde68a;color:inherit}
img.rv-noted{outline:3px solid #f59e0b;outline-offset:2px}
#rv-add{position:absolute;z-index:10000;display:none;font:13px -apple-system,system-ui,sans-serif;background:#111;color:#fff;border:0;border-radius:6px;padding:.3rem .6rem;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25)}
#rv-box,#rv-panel{font:13px/1.45 -apple-system,system-ui,sans-serif;color:#111;background:#fff;border:1px solid #ccc;border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.2);z-index:10001}
#rv-box{position:absolute;display:none;width:320px;padding:.6rem}
#rv-box blockquote{margin:0 0 .4rem;padding:.2rem .5rem;border-left:3px solid #f59e0b;color:#555;max-height:5.5em;overflow:hidden;font-size:12px}
#rv-box textarea{width:100%;box-sizing:border-box;height:5.5rem;font:inherit}
#rv-box .row,#rv-panel .row{display:flex;gap:.4rem;justify-content:flex-end;margin-top:.4rem}
#rv-box button,#rv-panel button{width:auto!important;display:inline-block!important;margin:0!important;font:inherit;font-size:12px;padding:.2rem .55rem;border:1px solid #bbb;border-radius:5px;background:#f6f6f6;cursor:pointer}
#rv-toggle{position:fixed;right:16px;bottom:16px;z-index:10002;font:600 13px -apple-system,system-ui,sans-serif;background:#f59e0b;color:#111;border:0;border-radius:18px;padding:.5rem .9rem;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.25)}
#rv-panel{position:fixed;right:16px;bottom:64px;width:360px;max-height:70vh;overflow:auto;display:none;padding:.6rem}
#rv-panel h4{margin:.1rem 0 .5rem;font-size:13px}
#rv-panel .hint{color:#666;font-size:12px;margin:0 0 .6rem}
#rv-panel .item{border-top:1px solid #eee;padding:.5rem 0}
#rv-panel .item.done{opacity:.5}
#rv-panel .q{color:#666;font-size:12px;border-left:3px solid #f59e0b;padding-left:.4rem;margin-bottom:.2rem;cursor:pointer;max-height:3em;overflow:hidden}
#rv-panel .note{white-space:pre-wrap}
</style>
<button id="rv-add">Dodaj uwagę</button>
<div id="rv-box"><blockquote></blockquote><textarea placeholder="Co poprawić? (Ctrl+Enter zapisuje)"></textarea>
<div class="row"><button data-x="cancel">Anuluj</button><button data-x="save">Zapisz</button></div></div>
<button id="rv-toggle">Uwagi</button>
<div id="rv-panel"><h4>Uwagi do artykułu</h4>
<p class="hint">Zaznacz fragment tekstu albo Alt+klik na obrazek, żeby dodać uwagę. <a href="/" target="_blank">lista</a> · <a href="/uwagi" target="_blank">wszystkie uwagi</a></p>
<div id="rv-list"></div></div>
<script>
(function(){
const STEM = {{ stem|tojson }};
const root = document.querySelector("article") || document.body;
const addBtn = document.getElementById("rv-add"), box = document.getElementById("rv-box");
const panel = document.getElementById("rv-panel"), toggle = document.getElementById("rv-toggle");
const list = document.getElementById("rv-list"), area = box.querySelector("textarea");
let pending = null, comments = [];
const inUi = n => [addBtn, box, panel, toggle].some(el => el.contains(n));
const esc = t => t.replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const norm = t => t.replace(/\\s+/g, " ").trim();

function textIndex(){
  const nodes = [], walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: n => inUi(n) || n.parentElement.closest("script,style") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
  let text = "", n;
  while((n = walker.nextNode())){ nodes.push([n, text.length]); text += n.data; }
  return {nodes, text};
}
function rangeFor(c, idx){
  const flat = idx.text.replace(/\\s/g, " "), q = c.quote.replace(/\\s+/g, " ");
  let at = -1, from = 0;
  while((from = flat.indexOf(q, from)) !== -1){ at = from; if(!c.prefix || flat.slice(Math.max(0, from - c.prefix.length), from).endsWith(c.prefix)) break; from += 1; }
  if(at < 0) return null;
  const pos = off => { for(let i = idx.nodes.length - 1; i >= 0; i--) if(idx.nodes[i][1] <= off) return [idx.nodes[i][0], off - idx.nodes[i][1]]; };
  const r = document.createRange(), a = pos(at), b = pos(at + q.length);
  r.setStart(a[0], a[1]); r.setEnd(b[0], b[1]); return r;
}
function paint(){
  document.querySelectorAll("img.rv-noted").forEach(i => i.classList.remove("rv-noted"));
  const idx = textIndex(), ranges = [];
  comments.forEach(c => {
    c._range = null;
    if(c.resolved) return;
    if(c.image){ document.querySelectorAll("img").forEach(i => { if(i.getAttribute("src") === c.image) i.classList.add("rv-noted"); }); return; }
    const r = rangeFor(c, idx); if(r){ c._range = r; ranges.push(r); }
  });
  if(window.CSS && CSS.highlights){ CSS.highlights.set("review-note", new Highlight(...ranges)); }
}
function render(){
  const open = comments.filter(c => !c.resolved).length;
  toggle.textContent = "Uwagi (" + open + ")";
  list.innerHTML = comments.length ? "" : "<p class='hint'>Brak uwag.</p>";
  comments.forEach(c => {
    const d = document.createElement("div");
    d.className = "item" + (c.resolved ? " done" : "");
    d.innerHTML = "<div class='q'>" + esc(c.image ? "[obrazek] " + c.image.split("/").pop() : c.quote) + "</div>"
      + "<div class='note'>" + esc(c.note) + "</div>"
      + "<div class='row'><button data-x='edit'>edytuj</button><button data-x='toggle'>" + (c.resolved ? "przywróć" : "zrobione") + "</button><button data-x='del'>usuń</button></div>";
    d.querySelector(".q").onclick = () => goTo(c);
    d.querySelector("[data-x=edit]").onclick = async () => { const t = prompt("Uwaga:", c.note); if(t !== null){ await api("PATCH", c.id, {note: t}); } };
    d.querySelector("[data-x=toggle]").onclick = () => api("PATCH", c.id, {resolved: !c.resolved});
    d.querySelector("[data-x=del]").onclick = () => { if(confirm("Usunąć uwagę?")) api("DELETE", c.id); };
    list.appendChild(d);
  });
  paint();
}
function goTo(c){
  let el = null;
  if(c.image) el = [...document.querySelectorAll("img")].find(i => i.getAttribute("src") === c.image);
  const rect = el ? el.getBoundingClientRect() : c._range && c._range.getBoundingClientRect();
  if(rect) window.scrollTo({top: window.scrollY + rect.top - 120, behavior: "smooth"});
}
async function load(){ comments = await (await fetch("/api/comments?stem=" + encodeURIComponent(STEM))).json(); render(); }
async function api(method, id, body){
  await fetch("/api/comments" + (id ? "/" + id : ""), {method, headers:{"Content-Type":"application/json"}, body: body ? JSON.stringify(body) : undefined});
  await load();
}
function hideAll(){ addBtn.style.display = "none"; box.style.display = "none"; pending = null; }
function openBox(x, y){
  box.querySelector("blockquote").textContent = pending.image ? "[obrazek] " + pending.image.split("/").pop() : pending.quote;
  area.value = ""; addBtn.style.display = "none";
  box.style.left = Math.min(x, window.scrollX + document.documentElement.clientWidth - 340) + "px";
  box.style.top = y + "px"; box.style.display = "block"; area.focus();
}
document.addEventListener("mouseup", e => {
  if(inUi(e.target)) return;
  setTimeout(() => {
    const sel = getSelection(), quote = norm(sel.toString());
    if(!quote || !sel.rangeCount){ if(box.style.display !== "block") hideAll(); return; }
    const r = sel.getRangeAt(0);
    if(!root.contains(r.commonAncestorContainer)) return;
    const pre = document.createRange(); pre.selectNodeContents(root); pre.setEnd(r.startContainer, r.startOffset);
    pending = {quote, prefix: pre.toString().replace(/\\s+/g, " ").slice(-40)};
    const rect = r.getBoundingClientRect();
    addBtn.style.left = (window.scrollX + rect.right - 40) + "px";
    addBtn.style.top = (window.scrollY + rect.bottom + 6) + "px";
    addBtn.style.display = "block";
  }, 0);
});
document.addEventListener("click", e => {
  if(e.altKey && e.target.tagName === "IMG" && !inUi(e.target)){
    e.preventDefault(); e.stopImmediatePropagation();
    pending = {image: e.target.getAttribute("src"), quote: ""};
    openBox(window.scrollX + e.clientX, window.scrollY + e.clientY + 8);
  }
}, true);
addBtn.onmousedown = e => e.preventDefault();
addBtn.onclick = () => { const r = addBtn.getBoundingClientRect(); openBox(window.scrollX + r.left, window.scrollY + r.bottom + 4); };
box.querySelector("[data-x=cancel]").onclick = hideAll;
async function save(){
  if(!pending || !area.value.trim()) return;
  const body = Object.assign({stem: STEM, note: area.value.trim()}, pending);
  hideAll(); getSelection().removeAllRanges(); await api("POST", null, body);
}
box.querySelector("[data-x=save]").onclick = save;
area.addEventListener("keydown", e => { if(e.key === "Enter" && (e.ctrlKey || e.metaKey)) save(); if(e.key === "Escape") hideAll(); });
toggle.onclick = () => { panel.style.display = panel.style.display === "block" ? "none" : "block"; };
load();
window.addEventListener("load", () => setTimeout(paint, 1500));
if(window.MathJax && MathJax.startup && MathJax.startup.promise) MathJax.startup.promise.then(() => setTimeout(paint, 300));
})();
</script>
"""

COMMENTS_PAGE = """<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8">
<title>Delta {{ version }} - uwagi</title><style>
body{font:14px/1.5 -apple-system,system-ui,sans-serif;margin:2rem auto;max-width:900px;color:#111;padding:0 1rem}
h1{font-size:1.3rem;margin:0 0 .25rem}h2{font-size:1rem;margin:1.6rem 0 .4rem}
a{color:#0a58ca;text-decoration:none}
.q{color:#666;border-left:3px solid #f59e0b;padding-left:.5rem;font-size:13px}
.item{padding:.5rem 0;border-bottom:1px solid #eee}.done{opacity:.45}
.note{white-space:pre-wrap}
textarea{width:100%;height:14rem;font:12px ui-monospace,monospace}
</style></head><body>
<h1>Uwagi - Delta {{ version }}</h1>
<p><a href="/">&larr; lista</a> · {{ open_total }} otwartych, {{ done_total }} zrobionych. Plik: <code>{{ path }}</code></p>
{% for stem, title, items in groups %}
<h2 id="{{ stem }}"><a href="/html/{{ stem }}" target="_blank">{{ title }}</a> <code>{{ stem }}</code></h2>
{% for c in items %}<div class="item{% if c.resolved %} done{% endif %}">
<div class="q">{% if c.image %}[obrazek] {{ c.image.split('/')[-1] }}{% else %}{{ c.quote }}{% endif %}</div>
<div class="note">{{ c.note }}</div></div>{% endfor %}
{% endfor %}
{% if export %}<h2>Do wklejenia (otwarte)</h2><textarea readonly>{{ export }}</textarea>{% endif %}
</body></html>"""


def comments_path() -> Path:
    return PATH.OUTPUT / COMMENTS_FILE


def load_comments() -> list[dict]:
    path = comments_path()
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_comments(items: list[dict]) -> None:
    PATH.OUTPUT.mkdir(parents=True, exist_ok=True)
    comments_path().write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def comments_export(groups) -> str:
    lines = []
    for stem, title, items in groups:
        open_items = [c for c in items if not c.get("resolved")]
        if not open_items:
            continue
        lines.append(f"{stem} ({title}):")
        for c in open_items:
            where = f"[obrazek {c['image'].split('/')[-1]}]" if c.get("image") else f"„{c['quote']}”"
            lines.append(f"- {where} -> {c['note']}")
        lines.append("")
    return "\n".join(lines).strip()


def run_job(action: str, argv: list[str]) -> None:
    proc = subprocess.Popen(
        [sys.executable, "-u", *argv], cwd=PATH.ROOT, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    for line in proc.stdout:
        with JOB_LOCK:
            JOB["lines"].append(line.rstrip("\n"))
    proc.wait()
    with JOB_LOCK:
        JOB["running"] = False
        JOB["code"] = proc.returncode


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
        open_counts: dict[str, int] = {}
        for c in load_comments():
            if not c.get("resolved"):
                open_counts[c["stem"]] = open_counts.get(c["stem"], 0) + 1
        links = PATH.OUTPUT / LINKS_FILE
        return render_template_string(
            INDEX,
            version=PATH.FIGURES.name.replace("-figures", ""),
            articles=issue_order(),
            checks=load_checks(),
            has_checks=bool(load_checks()),
            toc_name=toc.name if toc else "brak .toc",
            open_counts=open_counts,
            open_total=sum(open_counts.values()),
            actions=ACTIONS,
            links=links.read_text(encoding="utf-8") if links.is_file() else "",
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
        page = render_template(
            "static/template.html",
            title=article.title,
            author=article.author,
            content=article.html.read_text(encoding="utf-8"),
        )
        overlay = render_template_string(OVERLAY, stem=stem)
        if "</body>" in page:
            return page.replace("</body>", overlay + "</body>", 1)
        return page + overlay

    @app.route("/uwagi")
    def comments_page():
        items = load_comments()
        groups = []
        for article in issue_order():
            mine = [c for c in items if c["stem"] == article.stem]
            if mine:
                groups.append((article.stem, article.title, mine))
        return render_template_string(
            COMMENTS_PAGE,
            version=PATH.FIGURES.name.replace("-figures", ""),
            groups=groups,
            open_total=sum(1 for c in items if not c.get("resolved")),
            done_total=sum(1 for c in items if c.get("resolved")),
            path=comments_path(),
            export=comments_export(groups),
        )

    @app.get("/api/comments")
    def comments_list():
        stem = request.args.get("stem")
        return jsonify([c for c in load_comments() if stem is None or c["stem"] == stem])

    @app.post("/api/comments")
    def comments_add():
        data = request.get_json(force=True)
        if not data.get("stem") or not str(data.get("note", "")).strip():
            return jsonify({"error": "brak stem/note"}), 400
        item = {
            "id": uuid.uuid4().hex[:10],
            "stem": data["stem"],
            "quote": str(data.get("quote", ""))[:2000],
            "prefix": str(data.get("prefix", ""))[:80],
            "image": data.get("image") or None,
            "note": str(data["note"]).strip(),
            "resolved": False,
            "created": datetime.now().isoformat(timespec="seconds"),
        }
        with COMMENTS_LOCK:
            items = load_comments()
            items.append(item)
            save_comments(items)
        return jsonify(item), 201

    @app.route("/api/comments/<cid>", methods=["PATCH", "DELETE"])
    def comments_change(cid: str):
        with COMMENTS_LOCK:
            items = load_comments()
            item = next((c for c in items if c["id"] == cid), None)
            if item is None:
                abort(404)
            if request.method == "DELETE":
                items.remove(item)
            else:
                data = request.get_json(force=True)
                if "note" in data:
                    item["note"] = str(data["note"]).strip()
                if "resolved" in data:
                    item["resolved"] = bool(data["resolved"])
            save_comments(items)
        return jsonify({"ok": True})

    @app.get("/api/issue-id")
    def issue_id():
        from a11_admin_upload import find_issue_id
        version = PATH.FIGURES.name.replace("-figures", "")
        try:
            found = find_issue_id(version)
        except (SystemExit, Exception) as exc:
            return jsonify({"version": version, "id": None, "error": f"panel: {exc}"})
        return jsonify({"version": version, "id": found,
                        "error": None if found else f"brak numeru z data 01.{version[5:]}"})

    @app.post("/api/run/<action>")
    def run_action(action: str):
        act = ACTIONS.get(action)
        if act is None:
            abort(404)
        issue = str((request.get_json(silent=True) or {}).get("issue", "")).strip()
        if act["needs_issue"] and not issue.isdigit():
            return jsonify({"error": "podaj ID numeru"}), 400
        with JOB_LOCK:
            if JOB["running"]:
                return jsonify({"error": f"trwa juz: {JOB['action']}"}), 409
            JOB.update(action=action, running=True, lines=[f"$ {' '.join(act['argv'](issue))}"],
                       code=None, started=time.time())
        threading.Thread(target=run_job, args=(action, act["argv"](issue)), daemon=True).start()
        return jsonify({"ok": True})

    @app.get("/api/job")
    def job_status():
        with JOB_LOCK:
            return jsonify({k: JOB[k] for k in ("action", "running", "lines", "code")})

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
