#!/usr/bin/env python3
"""Checki layoutu wygenerowanych artykulow (Playwright, headless chromium)."""

import json
import logging
import threading
from werkzeug.serving import make_server
from a8_review import build_app
from articles import issue_order
from config import PATH
from helper import log_section

CHECK_PORT = 5099
CHECKS_FILE = "checks.json"

# Marginalia (przypisy przeniesione na margines) nie moga siegac nizej niz
# kolumna tresci - w druku margines konczy sie razem z tekstem. Tolerancja 4px
# na zaokraglenia layoutu.
MARGIN_TOLERANCE_PX = 4

# article.js przenosi kazdy blockquote#blockquote-N do div.article-input-margin
# i pozycjonuje absolutnie, UKLADAJAC W STOS: top = max(refTop-25, poprzedniBottom).
# Gdy marginaliow jest wiecej (albo sa dluzsze) niz tekstu obok, stos wychodzi
# ponizej konca kolumny tresci, a JS rozciaga wtedy .article-input-div. To jest
# dokladnie ten defekt, ktory chcemy wylapac - i widac go WYLACZNIE po
# wykonaniu JS-u, dlatego checki musza chodzic w przegladarce.
MARGIN_TOLERANCE_PX = 4

JS_SETTLED = """() => {
  const all = document.querySelectorAll('blockquote[id^="blockquote-"]');
  if (all.length === 0) return true;
  const inMargin = document.querySelectorAll('.article-input-margin blockquote');
  if (inMargin.length !== all.length) return false;
  return Array.from(inMargin).every(e => getComputedStyle(e).position === 'absolute');
}"""

PROBE = """() => {
  const out = [];
  const main = document.querySelector('.article-input-main-text');
  const margins = Array.from(document.querySelectorAll('.article-input-margin blockquote'));
  const mainBottom = main ? main.getBoundingClientRect().bottom + window.scrollY : null;

  let maxOver = null;
  if (mainBottom === null) {
    out.push({check: 'brak .article-input-main-text', detail: 'nie ma kolumny tresci'});
  } else {
    margins.forEach((el, i) => {
      const over = el.getBoundingClientRect().bottom + window.scrollY - mainBottom;
      if (maxOver === null || over > maxOver) maxOver = over;
      if (over > TOLERANCE) out.push({
        check: 'margines ponizej tresci',
        detail: `${el.id || 'blockquote[' + i + ']'} wychodzi ${Math.round(over)}px nizej`,
      });
    });
  }

  const doc = document.documentElement;
  if (doc.scrollWidth - doc.clientWidth > 1) out.push({
    check: 'poziome przewijanie',
    detail: `scrollWidth ${doc.scrollWidth} > clientWidth ${doc.clientWidth}`,
  });

  document.querySelectorAll('img').forEach(img => {
    if (!img.complete || img.naturalWidth === 0) out.push({
      check: 'obrazek sie nie wczytal',
      detail: img.getAttribute('src') || '(brak src)',
    });
  });

  document.querySelectorAll('mjx-merror').forEach(el => out.push({
    check: 'MathJax nie zrenderowal formuly',
    detail: (el.textContent || '').trim().slice(0, 120),
  }));

  const stray = document.querySelectorAll('.article-input-main-text blockquote').length;
  if (stray) out.push({
    check: 'blockquote nie przeniesiony na margines',
    detail: `${stray} zostalo w kolumnie tresci`,
  });

  return {problems: out, stats: {
    margins: margins.length,
    maxOver: maxOver === null ? null : Math.round(maxOver),
    imgs: document.querySelectorAll('img').length,
    formulas: document.querySelectorAll('mjx-container').length,
    cssLoaded: !!Array.from(document.styleSheets).find(s => (s.href || '').includes('article.css')),
  }};
}"""


def wait_for_mathjax(page) -> None:
    """
    MathJax v3 konczy typesetting dopiero po zdarzeniu load - bez tego czekania
    formuly nie maja jeszcze wymiarow i checki geometryczne klamia. Oficjalny
    hook to startup.promise; gdy MathJax nie wstal (brak sieci), nie blokujemy
    checkow - reszta asercji nadal ma sens.
    """
    try:
        page.wait_for_function("() => !!(window.MathJax && MathJax.startup"
                               " && MathJax.startup.promise)", timeout=20000)
        page.evaluate("() => MathJax.startup.promise")
        page.wait_for_timeout(200)
    except Exception as exc:
        print(f"#     (MathJax nie zgloszil gotowosci: {type(exc).__name__})")


class Server:
    """Flask w watku - checki nie wymagaja recznie odpalonego serwera."""

    def __init__(self, port: int):
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        self.srv = make_server("127.0.0.1", port, build_app())
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.srv.shutdown()


@log_section
def checks() -> dict:
    from playwright.sync_api import sync_playwright

    PATH.OUTPUT.mkdir(parents=True, exist_ok=True)
    articles = [a for a in issue_order() if a.html is not None]
    missing = [a.stem for a in issue_order() if a.html is None]
    for stem in missing:
        print(f"# SKIP {stem}: brak HTML")

    results: dict = {}
    probe = PROBE.replace("TOLERANCE", str(MARGIN_TOLERANCE_PX))

    with Server(CHECK_PORT), sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        for article in articles:
            page.goto(f"http://127.0.0.1:{CHECK_PORT}/html/{article.stem}",
                      wait_until="load", timeout=60000)
            wait_for_mathjax(page)
            try:
                page.wait_for_function(JS_SETTLED, timeout=20000)
            except Exception:
                print("#     (article.js nie ulozyl marginaliow w limicie czasu)")
            page.wait_for_timeout(200)
            probed = page.evaluate(probe)
            failed, stats = probed["problems"], probed["stats"]
            results[article.stem] = {"failed": failed, "stats": stats}
            mark = "OK" if not failed else f"{len(failed)} bledow"
            over = stats["maxOver"]
            print(f"# {article.position:2}. {article.stem:16} {mark:11}"
                  f" marginalia={stats['margins']:2}"
                  f" nadwis={'?' if over is None else str(over) + 'px':>8}"
                  f" css={'tak' if stats['cssLoaded'] else 'NIE'}"
                  f" img={stats['imgs']:2} formul={stats['formulas']:3}")
            for f in failed:
                print(f"#     - {f['check']}: {f['detail']}")
        browser.close()

    out = PATH.OUTPUT / CHECKS_FILE
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(v["failed"]) for v in results.values())
    print(f"# Zapisano {out} - artykulow: {len(results)}, bledow: {total}")
    return results


if __name__ == "__main__":
    checks()
