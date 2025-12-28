import re

def expand_rys_captions(content: str) -> str:
    r"""
    1. Usuwa CAŁĄ linię z definicją \def\rys#1{...} (jeśli taka jest).
    2. Zamienia wszystkie wywołania \rys{...} na:
         Rys. N. ...
       z poprawnym ogarnięciem zagnieżdżonych klamerek (np. \cite{...}).
    """

    # 1. Bezpieczne usunięcie linii z definicją \rys
    #    (nie dotykamy jej środka, tylko wywalamy całą linię)
    lines = content.splitlines(keepends=True)
    filtered_lines = []
    for line in lines:
        # jeśli w tej linii jest definicja \rys#1{...}, pomijamy ją
        if r'\def\rys#1{' in line:
            continue
        filtered_lines.append(line)
    content = ''.join(filtered_lines)

    # 2. Ręczne parsowanie wszystkich \rys{...}
    result_parts = []
    i = 0
    n = len(content)
    counter = 1
    token = r'\rys{'
    token_len = len(token)

    while i < n:
        j = content.find(token, i)
        if j == -1:
            # dalej nie ma \rys{...} – dopisujemy resztę tekstu i kończymy
            result_parts.append(content[i:])
            break

        # wszystko przed \rys zostaje jak było
        result_parts.append(content[i:j])

        # wchodzimy w środek klamerek po \rys{
        k = j + token_len
        depth = 1
        start_caption = k

        while k < n and depth > 0:
            ch = content[k]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            k += 1

        if depth != 0:
            # coś jest bardzo popsute (brak domykającej klamry) – dla bezpieczeństwa
            # nie ruszamy dalej tekstu
            result_parts.append(content[j:])
            break

        # środek między \rys{ ... } (bez tej końcowej klamry)
        caption = content[start_caption:k-1].strip()

        replacement = f"Rys. {counter}. {caption}"
        counter += 1

        result_parts.append(replacement)

        # przechodzimy za zamykającą klamrę
        i = k

    return ''.join(result_parts)
