import re
from bs4 import BeautifulSoup
from config import COLOR, NEWPAGE
from helper import log_section


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

    for footnotes in soup.find_all("section", {"id": "footnotes"}):
        for li_tag in footnotes.find_all("li"):
            if li_tag.has_attr("id"):
                match = re.match(r"^fn([0-9]+)$", li_tag["id"])
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
