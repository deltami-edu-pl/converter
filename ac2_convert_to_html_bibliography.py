import re


def fix_bibliography(content: str) -> str:
    """
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
    Zwraca zmodyfikowany content.
    """

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

    bib_index = build_bib_index(content)

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

    content = replace_cite_macros(content, bib_index)

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

    content = convert_thebibliography(content)

    return content
