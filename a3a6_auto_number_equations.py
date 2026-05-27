import re

def auto_number_equations(content: str) -> str:
    """
    Dla każdego środowiska:
        \begin{equation}
            ...
            \label{...}
            ...
        \end{equation}

    Jeśli nie ma \tag{}, dodaje \tag{1}, \tag{2}, ...
    Buduje mape label -> numer i podstawia \ref{X}/\eqref{X} na ten numer,
    bo pandoc by zwrocil "[X]" jako widoczny tekst linku (nie zna numerow
    z mathjaxowych label-ow).
    """

    eq_pattern = re.compile(
        r"\\begin\{equation\}(?P<body>.*?)\\end\{equation\}",
        flags=re.DOTALL
    )

    i = 1
    label_to_num: dict[str, int] = {}

    def repl(m: re.Match):
        nonlocal i
        body = m.group("body")

        # jeśli ma \tag – zostawiamy jak jest
        if r"\tag" in body:
            return m.group(0)

        # musi zawierać label, inaczej pomijamy
        if r"\label" not in body:
            return m.group(0)

        # zapamietujemy mapowanie label -> numer
        label_match = re.search(r"\\label\{([^}]+)\}", body)
        if label_match:
            label_to_num[label_match.group(1)] = i

        # wstawiamy \tag{n} tuż za \begin{equation}
        new_equation = (
            r"\begin{equation}"
            + f"\\tag{{{i}}}"
            + body
            + r"\end{equation}"
        )

        i += 1
        return new_equation

    content = eq_pattern.sub(repl, content)

    def ref_repl(m: re.Match) -> str:
        kind = m.group(1)  # "ref" lub "eqref"
        label = m.group(2)
        num = label_to_num.get(label)
        if num is None:
            return m.group(0)
        return f"({num})" if kind == "eqref" else str(num)

    content = re.sub(r"\\(ref|eqref)\{([^}]+)\}", ref_repl, content)

    return content
