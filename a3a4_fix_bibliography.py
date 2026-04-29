import re

# ---- KROK 1: Zbuduj mapę kluczy bibliografii -> numer ----
def build_bib_index(text: str) -> dict:
    match = re.search(
        r'\\begin\{thebibliography\}\{[^\}]*\}(.*?)\\end\{thebibliography\}',
        text,
        flags=re.DOTALL,
    )
    if not match:
        return {}

    body = match.group(1)

    # \bibitem{key} lub \bibitem[Opis]{key}
    keys = re.findall(
        r'\\bibitem(?:\[[^\]]*\])?\{([^\}]+)\}',
        body,
    )

    return {key: i + 1 for i, key in enumerate(keys)}

# ---- KROK 2: Zamiana \cite{...} na klikalne [n] ----
def replace_cite_macros(text: str, index: dict) -> str:
    if not index:
        return text

    def repl(m: re.Match) -> str:
        keys_str = m.group(1)  # np. "Magni_1648" albo "Magni_1648,Blander_1979"
        keys = [k.strip() for k in keys_str.split(',')]

        parts = []
        for k in keys:
            n = index.get(k)
            if n is None:
                # nie znaleziono w bibliografii – dajemy "?"
                parts.append('?')
            else:
                # [\href{#bib:Klucz}{n}]
                parts.append(r'\href{#bib:' + k + '}{' + str(n) + '}')

        # wynik w stylu: [1] lub [1, 2] (każda liczba osobno klikalna)
        return '[' + ', '.join(parts) + ']'

    return re.sub(r'\\cite\{([^\}]+)\}', repl, text)


# ---- KROK 3: Zamiana środowiska bibliografii ----
def convert_thebibliography(text: str) -> str:
    def repl(m: re.Match) -> str:
        body = m.group(1)

        # Zamieniamy każdy \bibitem[...] {key} na \item \label{bib:key}
        def bibitem_to_item(bm: re.Match) -> str:
            key = bm.group(1)
            # \item \label{bib:key} (dalej idzie treść pozycji)
            return r'\item \label{bib:' + key + '} '

        body_converted = re.sub(
            r'\\bibitem(?:\[[^\]]*\])?\{([^\}]+)\}',
            bibitem_to_item,
            body,
        )

        return (
            r'\section*{Bibliografia}' '\n'
            r'\begin{enumerate}' '\n'
            + body_converted +
            '\n' r'\end{enumerate}' '\n'
        )

    return re.sub(
        r'\\begin\{thebibliography\}\{[^\}]*\}(.*?)\\end\{thebibliography\}',
        repl,
        text,
        flags=re.DOTALL,
    )


def fix_xitem_enumerate(content: str) -> str:
    r"""
    Niektóre artykuły uzywaja niestandardowego \xitem do bibliografii:
        \begin{enumerate}[leftmargin=*,widest={D]}]\def\xitem#1 {\item[#1]}
            \xitem{[}A{]} ... \xitem{[}B{]} ...
        \end{enumerate}
    Pandoc krztusi sie na \def w naglowku enumerate i opcjach z {D]}, w efekcie
    cala lista znika z HTML. Zamieniamy enumerate na description (pandoc renderuje
    jako <dl> z <dt> dla etykiet, wiec [A], [B] zostaja widoczne):
        - \def\xitem... -> usuniete
        - \xitem{[}X{]} -> \item[{[}X{]}]
        - cale enumerate -> description
    """
    def repl(m: re.Match) -> str:
        body = m.group(1)
        body = re.sub(r"\\def\\xitem#1\s*\{\\item\[#1\]\}", "", body)
        body = re.sub(r"\\xitem(\{\[\}\w+\{\]\})", r"\\item[\1]", body)
        return r"\begin{description}" + body + r"\end{description}"

    return re.sub(
        r"\\begin\{enumerate\}\[[^\[]*?widest=\{[^}]+\}[^\[]*?\](.*?)\\end\{enumerate\}",
        repl,
        content,
        flags=re.DOTALL,
    )


def fix_bibliography(content: str) -> str:
    r"""
    Poprawia bibliografię LaTeX:
    - mapuje \bibitem{key} -> numer (1, 2, 3, ...)
    - zamienia \cite{key1,key2} -> [1, 2] z klikalnymi linkami
      (każda liczba jest \href{#bib:key}{n})
    - zamienia środowisko thebibliography na:
        \section*{Bibliografia}
        \begin{enumerate}
          \item \label{bib:key1} ...
          ...
        \end{enumerate}
    - normalizuje \xitem-bibliografie na zwykla enumerate
    Zwraca zmodyfikowany content.
    """

    bib_index = build_bib_index(content)

    content = replace_cite_macros(content, bib_index)

    content = convert_thebibliography(content)

    content = fix_xitem_enumerate(content)

    return content
