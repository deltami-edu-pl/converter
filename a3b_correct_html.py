import re
from bs4 import BeautifulSoup, NavigableString
from config import COLOR, NEWPAGE
from helper import log_section


def move_labels_above_images(soup):
    r"""
    Przenosi kotwice <span data-label=... id=...></span> NAD obrazek, do ktorego
    sie odnosi.

    W zrodle \label{fig:x} stoi zwykle PO \podpis{...}, wiec pandoc emituje
    kotwice pod obrazkiem. Klikniecie w~"rys.~\ref{fig:x}" przewijalo wtedy
    strone za nisko - obrazek zostawal nad viewportem. Kotwica jest pusta,
    wiec samo przeniesienie nie zmienia nic w~wygladzie.
    """
    moved = 0
    for span in list(soup.find_all("span", attrs={"data-label": True})):
        if span.get_text(strip=True):
            continue  # nie kotwica, a realna tresc - nie ruszamy

        # Kontener MUSI byc realnym pojemnikiem figury. Wczesniej byl tu
        # fallback na span.parent.parent - dla kotwicy w zwyklym akapicie
        # kontenerem stawal sie caly div artykulu, find("img") lapal pierwszy
        # obrazek w tekscie i kotwica twierdzenia/sekcji byla wyrywana ze zdania
        # i przenoszona na poczatek artykulu. \ref do niej przewijal wtedy
        # w zupelnie inne miejsce.
        container = span.find_parent("div", class_="minipage")
        if container is None:
            container = span.find_parent("blockquote")
        if container is None:
            # ostatnia opcja: wlasny akapit kotwicy, ale tylko gdy sam zawiera
            # obrazek - wtedy wiadomo, ze kotwica dotyczy tej figury
            parent = span.parent
            if parent is not None and parent.name == "p" and parent.find("img"):
                container = parent
        if container is None:
            continue

        img = container.find("img")
        if img is None:
            continue

        # czy kotwica jest juz przed obrazkiem?
        order = [n for n in container.descendants if n is span or n is img]
        if order and order[0] is span:
            continue

        # wstaw przed najwyzszym przodkiem obrazka bedacym dzieckiem kontenera
        target = img
        while target.parent is not container and target.parent is not None:
            target = target.parent

        old_parent = span.parent
        target.insert_before(span.extract())
        moved += 1

        # akapit, w ktorym wisiala sama kotwica, zostaje pusty
        if (
            old_parent is not None
            and old_parent.name == "p"
            and not old_parent.get_text(strip=True)
            and old_parent.find("img") is None
        ):
            old_parent.decompose()

    if moved:
        print(f"- Kotwice data-label przeniesione nad obrazek: {moved}")


@log_section
def replace_article_in_newpage(soup, title="", author="", url=""):
    with open(NEWPAGE, "r") as file:
        newpage_content = file.read()

    # newpage_content = re.sub(r'\:root \{ --primary-color\: \#[A-Za-z0-9]{6}', ":root { --primary-color: #"+color, newpage_content)

    # Parse the HTML content using BeautifulSoup
    newpagesoup = BeautifulSoup(newpage_content, "html.parser")

    titletag = newpagesoup.find("a", "article-title")
    if titletag is not None:
        titletag.string.replace_with(title)
        titletag["href"] = url

    titletag = newpagesoup.find("title")
    if titletag is not None:
        titletag.string.replace_with(title)

    if author is not None:
        authortag = newpagesoup.find("span", "author")
        if authortag is not None:
            if authortag.find("a") is not None:
                authortag.find("a").string.replace_with(author)
    else:
        print("ERROR! nie ma autora!")

    if newpagesoup.find("article", "article-input") is None:
        print("ERROR! nie ma article.article-input w " + NEWPAGE)
    else:
        if soup.find("article", "article-input") is None:
            print("ERROR! nie ma article.article-input w tym co wstawiam!")
        else:
            newpagesoup.find("article", "article-input").replace_with(
                soup.find("article", "article-input")
            )

    return newpagesoup


def add_links_to_delta(soup):
    span_maths = soup.find_all("span", "math")
    for span in span_maths:
        if span.find_parent("a") is None:
            month = ""
            match = re.match(r"\\\(\\Delta\_\{([0-9]+)\}\^\{([0-9]+)\}", span.text)
            if not match:
                match = re.match(r"\\\(\\Delta\_\{([0-9]+)\}\^([0-9])", span.text)
            if match:
                year = match[1]
                month = match[2]

            match = re.match(r"\\\(\\Delta\^\{([0-9]+)\}\_\{([0-9]+)\}", span.text)
            if not match:
                match = re.match(r"\\\(\\Delta\^([0-9])\_\{([0-9]+)\}", span.text)
            if match:
                year = match[2]
                month = match[1]

            if not month == "":
                if int(year) < 74:
                    year = "20" + year
                else:
                    year = "19" + year
                if int(month) < 10:
                    month = "0" + str(int(month))
                a_tag = soup.new_tag("a")
                a_tag["href"] = "https://deltami.edu.pl/" + year + "/" + month + "/"
                span.replace_with(a_tag)
                a_tag.append(span)
                print(
                    "- dodałem link: "
                    + a_tag["href"]
                    + " do "
                    + span.text
                    + " (można doprecyzować)"
                )
    return soup


ROW_GAP_PX = 12
SAPER_MAX_WIDTH_PX = 200
CAPTION_LABEL_RE = re.compile(r"^\s*Rys\.?\s*\d+\b")


def _top_child(node, container):
    while node.parent is not container:
        node = node.parent
    return node


def _is_blank(node) -> bool:
    if getattr(node, "name", None) is None:
        return not str(node).strip()
    return node.name != "img" and node.find("img") is None and not node.get_text(strip=True)


def _add_style(tag, style: str):
    current = tag.get("style", "").strip().rstrip(";")
    tag["style"] = f"{current};{style}" if current else style


def limit_saper_images(soup):
    for img in soup.find_all("img", src=re.compile(r"/saper-")):
        _add_style(img, f"max-width:{SAPER_MAX_WIDTH_PX}px")


def move_captions_below_images(soup):
    """<p>Rys. N<img/></p> -> <p><img/>Rys. N</p>; w marginesie z <br/> przed podpisem."""
    for p in soup.find_all("p"):
        imgs = p.find_all("img")
        if not imgs:
            continue
        first = _top_child(imgs[0], p)
        before = list(first.previous_siblings)[::-1]
        if any(getattr(n, "name", None) and (n.name == "img" or n.find("img")) for n in before):
            continue
        label = "".join(n.get_text() if getattr(n, "name", None) else str(n) for n in before)
        if not CAPTION_LABEL_RE.match(label):
            continue
        last = _top_child(imgs[-1], p)
        nodes = [n.extract() for n in before]
        if isinstance(nodes[0], NavigableString):
            nodes[0] = NavigableString(str(nodes[0]).lstrip())
        target = last
        if p.find_parent("blockquote") is not None:
            br = soup.new_tag("br")
            target.insert_after(br)
            target = br
        for node in nodes:
            target.insert_after(node)
            target = node


def make_image_rows(soup):
    """Kilka obrazkow w jednym akapicie tresci -> obok siebie (CSS ma img display:block)."""
    for p in list(soup.find_all("p")):
        if p.find_parent("blockquote") is not None:
            continue
        imgs = p.find_all("img")
        if len(imgs) < 2:
            continue
        row = soup.new_tag("span")
        row["class"] = "image-row"
        row["style"] = (
            "display:flex;flex-wrap:wrap;justify-content:center;"
            f"align-items:center;gap:{ROW_GAP_PX}px"
        )
        tops = []
        for img in imgs:
            top = _top_child(img, p)
            if top not in tops:
                tops.append(top)
        tops[0].insert_before(row)
        for img in imgs:
            share = f"calc({100 / len(imgs):.0f}% - {ROW_GAP_PX}px)"
            limit = re.search(r"max-width:\s*([^;]+)", img.get("style", ""))
            if limit:
                img["style"] = img["style"].replace(limit.group(0), f"max-width:min({limit.group(1).strip()}, {share})")
                _add_style(img, "margin:0")
            else:
                _add_style(img, f"margin:0;max-width:{share}")
            row.append(img.extract())
        for top in tops:
            if top.parent is not None and top is not row:
                for br in top.find_all("br"):
                    br.extract()
                if _is_blank(top):
                    top.extract()
        for sib in list(row.next_siblings):
            if getattr(sib, "name", None) == "br":
                sib.extract()
            elif getattr(sib, "name", None) is None and not str(sib).strip():
                continue
            else:
                break


def _leading_strong(p, pattern: str):
    first = next((c for c in p.children if getattr(c, "name", None) or str(c).strip()), None)
    if getattr(first, "name", None) == "strong" and re.match(pattern, first.get_text(strip=True)):
        return first
    return None


def wrap_inline_exercises(soup):
    """
    <p><strong>Zadanie.</strong>...</p>...<p><strong>Rozwiązanie.</strong>...</p><p><img/></p>
    w zwyklym artykule -> div.exercise ze zwijanym rozwiazaniem (article.js).
    """
    for sol_p in list(soup.find_all("p")):
        if sol_p.find_parent("div", "exercise") is not None:
            continue
        sol_label = _leading_strong(sol_p, r"^Rozwiązani[ea](\s+zada[nń]\w*)?\.?$")
        if sol_label is None:
            continue
        task_p = sol_p.find_previous_sibling("p")
        while task_p is not None and _leading_strong(task_p, r"^Zadanie\b") is None:
            task_p = task_p.find_previous_sibling("p")
        if task_p is None:
            continue
        task_nodes, node = [], task_p
        while node is not sol_p:
            task_nodes.append(node)
            node = node.next_sibling
        sol_nodes = [sol_p]
        node = sol_p.next_sibling
        while node is not None and (
            (getattr(node, "name", None) is None and not str(node).strip())
            or (getattr(node, "name", None) == "p" and node.find("img") is not None and not node.get_text(strip=True))
        ):
            sol_nodes.append(node)
            node = node.next_sibling
        task_label = _leading_strong(task_p, r"^Zadanie\b")
        header_text = task_label.get_text(strip=True).rstrip(".")
        task_label.extract()
        sol_label.extract()
        wrapper = BeautifulSoup(
            f'<div class="exercise"><!-- EXERCISE BEGIN -->\n<header class="exercise">{header_text}</header>'
            '<!-- EXERCISE MIDDLE--> <header class="answer"><a href="javascript:void(0)">Rozwiązanie</a></header>'
            '<div class="answer-content"></div></div>',
            "html.parser",
        ).div
        task_p.insert_before(wrapper)
        middle = wrapper.find("header", "answer")
        for n in task_nodes:
            middle.insert_before(n.extract())
        content = wrapper.find("div", "answer-content")
        for n in sol_nodes:
            content.append(n.extract())


def correct_html(html_content) -> str:
    # pandoc zamiast \qed tworzy 0[], a nie []
    html_content = html_content.replace("0" + "\u25fb", "\u25fb")
    html_content = html_content.replace("deltaColor", "var(--primary-color)")
    html_content = html_content.replace("#" + COLOR, "var(--primary-color)")

    # pandoc dla \textcolor[HTML]{HEX}{X} emituje style="color: HEX" bez
    # poprzedzajacego #, co jest nieprawidlowym CSS i przegladarka ignoruje
    # kolor. Dopisujemy # przed 3- lub 6-cyfrowym hexem w style="color: ...".
    html_content = re.sub(
        r'(style="[^"]*color:\s*)([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})(\s*[;"])',
        r"\1#\2\3",
        html_content,
    )

    html_content = re.sub(
        r'<div class="answer">\s*\n?\s*<p>\s*<strong>Rozwiązanie(\s+[0-9]+)?</strong>\. ',
        '<!-- EXERCISE MIDDLE--> <header class="answer"><a href="javascript:void(0)">Rozwiązanie</a></header><div class="answer-content">\n',
        html_content,
        flags=re.DOTALL,
    )

    html_content = re.sub(
        r'<div class="exercise">\s?<p><strong>Zadanie(\s*[0-9]+)?</strong>.\s*<span>(M\s+[0-9]+)\.</span>',
        r'<div class="exercise"><!-- EXERCISE BEGIN -->\n<header class="exercise">Zadanie \2</header><p>',
        html_content,
        flags=re.DOTALL,
    )
    html_content = re.sub(
        r'<div class="exercise">\s?<p><strong>Zadanie(\s*[0-9]+)?</strong>.\s*<span>(F\s+[0-9]+)\.</span>',
        r'<div class="exercise"><!-- EXERCISE BEGIN -->\n<header class="exercise">Zadanie \2</header><p>',
        html_content,
        flags=re.DOTALL,
    )

    if re.findall('<header class="exercise">Zadanie M', html_content):
        autor1 = "XXX"
        autor2 = "XXX"
        for a in re.findall(r"(<span>Przygotował (.*?)</span>)", html_content):
            if autor1 == "XXX":
                autor1 = a[1]
                html_content = html_content.replace(a[0], "")
            else:
                if autor2 == "XXX":
                    autor2 = a[1]
                    html_content = html_content.replace(a[0], "")

        html_content = re.sub(
            r'(<div class="exercise"><header class="exercise">Zadanie M)',
            r"<p><span><em>Przygotował " + autor1 + r"</em></span></p>\1",
            html_content,
            1,
            flags=re.DOTALL,
        )
        html_content = re.sub(
            r'(<div class="exercise"><header class="exercise">Zadanie F)',
            r"<hr /><p><span><em>Przygotował " + autor2 + r"</em></span></p>\1",
            html_content,
            1,
            flags=re.DOTALL,
        )

    soup = BeautifulSoup(html_content, "html.parser")

    # owin naglowek "Bibliografia" + wszystko az do nastepnego naglowka w
    # <div class="erratum"> - korzystamy z istniejacego stylu erraty, zeby
    # bibliografia dostala szare tlo i padding jak inne wyrozniajace sie
    # bloki. Heading dostaje id="bibliografia" z pandoca (slugifikacja
    # \section*{Bibliografia}).
    biblio_heading = soup.find(["h1", "h2", "h3"], id="bibliografia")
    if biblio_heading is not None:
        wrapper = soup.new_tag("div")
        wrapper["class"] = "erratum"
        biblio_heading.insert_before(wrapper)
        node = biblio_heading
        while node is not None:
            nxt = node.next_sibling
            if (
                getattr(node, "name", None) in ("h1", "h2", "h3")
                and node is not biblio_heading
            ):
                break
            wrapper.append(node.extract())
            node = nxt

    title = ""
    author = ""
    url = "#"
    if soup.find("h1", "title"):
        title_tag = soup.find("h1", "title")
        for span_tag in title_tag.find_all("span"):
            if span_tag.string is not None and span_tag.string.strip() == "":
                span_tag.extract()
        title = title_tag.get_text()

    if soup.find("p", "author"):
        author = soup.find("p", "author").string

    for header_tag in soup.find_all("header", {"id": "title-block-header"}):
        header_tag.extract()

    real_notes = {}
    for footnotes in soup.find_all("section", {"id": "footnotes"}):
        for li_tag in footnotes.find_all("li"):
            if li_tag.has_attr("id"):
                match = re.match(r"^fn([0-9]+)$", li_tag["id"])
                if match and li_tag.find("blockquote") is None:
                    if li_tag.find("a", "footnote-back") is not None:
                        li_tag.find("a", "footnote-back").extract()
                    real_notes[match.group(1)] = li_tag.extract()
                    continue
                if match:
                    for blockquote in li_tag.find_all("blockquote"):
                        blockquote["id"] = "blockquote-" + match.group(1)
                        del blockquote["class"]
                        blockquote["class"] = "blockquote-margin"
                if li_tag.find("a", "footnote-back") is not None:
                    li_tag.find("a", "footnote-back").extract()
                li_tag.replaceWithChildren()

        footnotes.name = "div"
        del footnotes["class"]
        footnotes["class"] = "article-input-margin"
        for hr in footnotes.findChildren("hr", recursive=False):
            hr.replaceWithChildren()

        if footnotes.find("ol") is not None:
            footnotes.find("ol").replaceWithChildren()

    for footnote_ref in soup.find_all("a", "footnote-ref"):
        block_id = "blockquote-"
        if footnote_ref.has_attr("id"):
            match = re.match(r"^fnref([0-9]+)$", footnote_ref["id"])
            if match and match.group(1) in real_notes:
                marker = "*" * (list(real_notes).index(match.group(1)) + 1)
                sup = soup.new_tag("sup")
                sup.string = marker
                footnote_ref.replace_with(sup)
                note = soup.new_tag("p", style="font-size:0.85em")
                note.append(marker + " ")
                for child in list(real_notes[match.group(1)].children):
                    if getattr(child, "name", None) == "p":
                        child.replace_with_children()
                for child in list(real_notes[match.group(1)].children):
                    note.append(child.extract())
                body = soup.find("body")
                (body if body is not None else soup).append(note)
                continue
            if match:
                block_id = block_id + match.group(1)

        span = BeautifulSoup(
            "<span id='span-" + block_id + "' class='span-blockquote-ref'></span>",
            "html.parser",
        )
        footnote_ref.replace_with(span)

    for footnotes in soup.find_all("div", "article-input-margin"):
        for blockquote in footnotes.find_all("blockquote"):
            if blockquote.has_attr("id"):
                span = soup.find("span", {"id": "span-" + blockquote["id"]})
                if span is not None:
                    p = span.find_parent("p")
                    if p is not None:
                        if span.previous_sibling is None:
                            p.insert_before(blockquote)
                        else:
                            while (
                                p.next_sibling is not None
                                and p.next_sibling.name == "blockquote"
                            ):
                                p = p.next_sibling
                            p.insert_after(blockquote)
                    else:
                        span.insert_after(blockquote)

    for span_tag in soup.find_all("span"):
        if span_tag.string == ",":
            span_tag.replace_with(",")

    for span_tag in soup.find_all("span"):
        if span_tag.has_attr("style") and span_tag["style"] == "color: blue":
            del span_tag["style"]
            span_tag.name = "strong"
        if (
            span_tag.has_attr("style")
            and span_tag["style"] == "color: blue"
            and span_tag.find("strong")
        ):
            span_tag.replaceWithChildren()

    limit_saper_images(soup)
    move_captions_below_images(soup)
    make_image_rows(soup)
    wrap_inline_exercises(soup)

    # <p><img/>...caption...</p>  ->  <p><img/><span class="image-caption">caption</span></p>
    # (zdejmuje wiodace <br/> po obrazku, owija reszte jesli jest tam jakikolwiek tekst)
    # przypadki:
    #   <p><img/></p>                  -> pominiete (brak tresci, chyba ze nastepny <p>
    #                                     zaczyna sie od "Rys. N" -> wtedy scal go jako caption)
    #   <p><img/>\n</p>                -> jw.
    #   <p><img/><br/></p>             -> pominiete (br bez tresci; <br/> zostaje)
    #   <p><img/>caption</p>           -> owiniete
    #   <p><img/><br/>caption</p>      -> owiniete, <br/> usuniety
    #   <p><img/><br/><br/>caption</p> -> owiniete, oba <br/> usuniete
    for p in list(soup.find_all("p")):
        img = p.find("img")
        if img is None:
            continue
        # nie owijaj obrazkow w marginesach (blockquote-margin) - tam image-caption
        # nie ma sensu i CSS dla marginesow ma swoje rzadzace style
        if p.find_parent("blockquote") is not None:
            continue
        # img moze byc opakowany w <span> - znajdz najwyzszego przodka ktory jest
        # bezposrednim dzieckiem <p>, zeby patrzec na rodzenstwa w <p>, nie w <span>
        anchor = img
        while anchor.parent is not p:
            anchor = anchor.parent
        siblings = list(anchor.next_siblings)
        leading_brs = []
        while siblings and getattr(siblings[0], "name", None) == "br":
            leading_brs.append(siblings.pop(0))
        has_content = any(
            (getattr(n, "name", None)) or str(n).strip() for n in siblings
        )
        # jesli po obrazku nic nie ma, sprobuj zaanektowac nastepny <p> jako podpis
        if not has_content:
            next_p = p.find_next_sibling("p")
            if next_p is not None and re.match(
                r"Rys\.?\s*\d", next_p.get_text().strip()
            ):
                for child in list(next_p.children):
                    p.append(child.extract())
                next_p.extract()
                # po dolaczeniu rebuilduj rodzenstwa
                siblings = list(anchor.next_siblings)
                leading_brs = []
                while siblings and getattr(siblings[0], "name", None) == "br":
                    leading_brs.append(siblings.pop(0))
                has_content = any(
                    (getattr(n, "name", None)) or str(n).strip() for n in siblings
                )
        if not has_content:
            continue
        for br in leading_brs:
            br.extract()
        caption_nodes = [n.extract() for n in siblings]
        span = soup.new_tag("span")
        span["class"] = "image-caption"
        for node in caption_nodes:
            span.append(node)
        anchor.insert_after(span)

    move_labels_above_images(soup)

    article = soup.find("body")
    if article is None:
        print("- !!! Nie ma body!")
        return

    article.name = "article"
    article["class"] = ["article-input"] + ["article-from-tex"]

    article_div = soup.new_tag("div")
    article_div["class"] = "article-input-div"
    if article.find("div", "article-input-margin"):
        article_div.append(article.find("div", "article-input-margin"))
    else:
        print("- !!! Uwaga! Nie ma div.article-input-margin")

    soup = add_links_to_delta(soup)

    main_text = soup.new_tag("div")
    main_text["class"] = "article-input-main-text"
    for el in article.findChildren(recursive=False):
        main_text.append(el.extract())
        main_text.append("\n\n")

    # Jesli ostatni blockquote-margin zawiera obrazek a jego span-anchor jest
    # w ostatnim paragrafie - przesun sam span ~5 paragrafow wstecz, zeby obrazek
    # w marginesie nie konczyl sie ponizej tekstu artykulu. Blockquote zostawiamy.
    blockquotes = main_text.find_all("blockquote", "blockquote-margin")
    if blockquotes:
        last_bq = blockquotes[-1]
        if last_bq.find("img") is not None and last_bq.has_attr("id"):
            anchor = main_text.find("span", {"id": "span-" + last_bq["id"]})
            paragraphs = main_text.find_all("p", recursive=False)
            if anchor is not None and paragraphs:
                anchor_p = anchor.find_parent("p")
                if anchor_p is paragraphs[-1]:
                    span_target = paragraphs[max(0, len(paragraphs) - 2)]
                    anchor.extract()
                    span_target.insert(0, anchor)

    article_div.insert(0, main_text)

    article.append(article_div)

    newsoup = replace_article_in_newpage(soup, title, author, url)

    return str(newsoup)
