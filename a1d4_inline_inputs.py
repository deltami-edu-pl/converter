import re
from config import PATH

MAX_DEPTH = 3


def strip_comments(content: str) -> str:
    r"""
    Ten sam strip komentarzy co w a1d3_clean_tex, ale odpalany PRZED
    inline_inputs. Bez tego zakomentowany \input (09-miskiewicz:
    `...{doppler/d-crop}%\textcolor{black}{\input{doppler/rys-music.tex}}`)
    zostalby wklejony, a jego dalsze linie - w przeciwienstwie do pierwszej -
    wyladowalyby POZA komentarzem, jako aktywny kod.
    """
    content = re.sub(r"(?<=[^\\])%.*", "%", content)
    content = re.sub(r"\n([ \t]*%\n)*", "\n", content)
    content = re.sub(r"(?<=\~)\%\n", "", content, flags=re.DOTALL)
    return content


def _resolve(path: str):
    r"""
    Sciezka do pliku wskazanego przez \input{...}, o ile wolno go wkleic.

    Wklejamy TYLKO pliki z podkatalogow dropu (np. doppler/rys-doppler.tex) -
    to sa fragmenty rysunkow nalezace do artykulu. NIE wklejamy \input-ow
    wskazujacych na inne artykuly: 03-kat-o robi `\input 04-tjz`, a
    07-krukowski `\input 08-rajkowski` (lancuchowanie kolejnych artykulow
    w druku). Wklejenie ich zdublowaloby caly nastepny artykul w poprzednim,
    dlatego wymagamy separatora katalogu w sciezce.
    """
    if "/" not in path:
        return None

    candidate = PATH.SOURCE / path
    for p in (candidate, candidate.with_suffix(".tex")):
        if p.is_file():
            return p
    return None


def inline_inputs(content: str, depth: int = 0) -> str:
    r"""
    Zamienia \input{podkatalog/plik} na tresc tego pliku.

    a1d3_clean_tex strippuje wszystkie \input, wiec bez tego kroku rysunki
    trzymane w osobnych plikach przepadaja bez sladu (09-miskiewicz: dwa
    tikzpicture w doppler/rys-doppler.tex i doppler/rys-keyboard.tex).
    Po wklejeniu tikzpicture jest juz w tresci artykulu, wiec a2 wyrenderuje
    go do PNG, a a3a3 podmieni na <img>.

    Nierozwiazane \input zostawiamy - clean_tex usunie je jak dotychczas.
    """
    if depth >= MAX_DEPTH:
        return content

    def repl(m: re.Match) -> str:
        path = m.group(1).strip()
        resolved = _resolve(path)
        if resolved is None:
            return m.group(0)
        print(f"#   inline \\input{{{path}}} <- {resolved}")
        inner = strip_comments(resolved.read_text(encoding="utf-8"))
        return inline_inputs(inner, depth + 1)

    return re.sub(r"\\input\{([^}]*)\}", repl, content)
