#!/usr/bin/env python3

import re
from bs4 import BeautifulSoup
from helper import log_section


def _li_inner_html(li) -> str:
    """Zawartosc <li> bez samych tagow <li></li>."""
    return "".join(str(child) for child in li.contents).strip()


@log_section
def convert_zadania(content: str) -> str:
    """
    Jesli artykul ma na marginesie blok "Wskazowki do zadan" z lista <ol>
    a w tresci osobna liste zadan, paruje je i przerzuca wskazowki pod zadania
    jako rozwijalna sekcja "Wskazowka". Margines ze wskazowkami (razem z
    tytulem) jest usuwany, jego span-anchor tez.

    Bezpieczne dla artykulow ktore nie pasuja do tego wzorca - wtedy zwraca
    content bez zmian.
    """
    soup = BeautifulSoup(content, "html.parser")

    hints_blockquote = None
    for bq in soup.find_all("blockquote", "blockquote-margin"):
        text = bq.get_text()
        if re.search(r"Wskaz[óo]wk[aiy]\s+do\s+zada", text) and bq.find("ol"):
            hints_blockquote = bq
            break
    if hints_blockquote is None:
        return content

    hints_list = hints_blockquote.find("ol")
    hints = hints_list.find_all("li", recursive=False)

    # preferuj <ol> ktore jest siostra po <p><strong>Zadania</strong></p>,
    # bo artykul moze miec inne wczesniejsze listy <ol> (np. punkty
    # twierdzenia w 14-bzdega) ktore nie sa zadaniami.
    problems_list = None
    for p in soup.find_all("p"):
        strong = p.find("strong")
        if strong is None:
            continue
        if not re.match(r"\s*zadania\b", strong.get_text(strip=True), re.IGNORECASE):
            continue
        sib = p.find_next_sibling()
        while sib is not None:
            if getattr(sib, "name", None) == "ol":
                problems_list = sib
                break
            sib = sib.find_next_sibling()
        if problems_list is not None:
            break

    # fallback: pierwsza top-level <ol> poza blockquote
    if problems_list is None:
        for ol in soup.find_all("ol"):
            if ol.find_parent("blockquote") is not None:
                continue
            problems_list = ol
            break
    if problems_list is None:
        return content

    problems = problems_list.find_all("li", recursive=False)
    if not problems or not hints:
        return content

    for problem_li, hint_li in zip(problems, hints):
        problem_inner = _li_inner_html(problem_li)
        hint_inner = _li_inner_html(hint_li)
        wrapper = BeautifulSoup(
            f"""<div class="exercise"><!-- EXERCISE BEGIN -->
{problem_inner}
<!-- EXERCISE MIDDLE--> <header class="answer"><a href="javascript:void(0)">Wskazówka</a></header><div class="answer-content">
{hint_inner}
</div>
</div>""",
            "html.parser",
        )
        problem_li.clear()
        problem_li.append(wrapper)

    # usun tylko sam tytul "Wskazowki do zadan" i lista <ol>; reszta moze
    # zawierac inne tresci (obrazki, logo, afiliacja - np. 14-bzdega ma w
    # tym samym \marg{} logo KMO + rysunek trojkata + wskazowki).
    for strong in hints_blockquote.find_all("strong"):
        if re.search(r"Wskaz[óo]wk[aiy]\s+do\s+zada", strong.get_text(strip=True)):
            # usun caly <p> zawierajacy ten <strong>, jezeli istnieje;
            # inaczej tylko sam <strong>
            container = strong.find_parent("p")
            (container or strong).decompose()
            break
    hints_list.decompose()

    # jezeli po wyjeciu wskazowek nic sensownego nie zostalo - usun caly
    # blockquote (i jego span-anchor), zeby nie zostawial pustego marginesu
    leftover = hints_blockquote.get_text(strip=True)
    has_media = hints_blockquote.find("img") is not None
    if not leftover and not has_media:
        bq_id = hints_blockquote.get("id", "")
        if bq_id:
            anchor = soup.find("span", {"id": "span-" + bq_id})
            if anchor is not None:
                anchor.decompose()
        hints_blockquote.decompose()

    return str(soup)
