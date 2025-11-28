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
    """

    eq_pattern = re.compile(
        r"\\begin\{equation\}(?P<body>.*?)\\end\{equation\}",
        flags=re.DOTALL
    )

    i = 1

    def repl(m: re.Match):
        nonlocal i
        body = m.group("body")

        # jeśli ma \tag – zostawiamy jak jest
        if r"\tag" in body:
            return m.group(0)

        # musi zawierać label, inaczej pomijamy
        if r"\label" not in body:
            return m.group(0)

        # wstawiamy \tag{n} tuż za \begin{equation}
        new_equation = (
            r"\begin{equation}"
            + f"\\tag{{{i}}}"
            + body
            + r"\end{equation}"
        )

        i += 1
        return new_equation

    return eq_pattern.sub(repl, content)
