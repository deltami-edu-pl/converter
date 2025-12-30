import re


def clean_tex(content: str) -> str:
    # usuwa zawartosc komentarzy oraz linie, w ktorych sa tylko komentarze
    content = re.sub(r"(?<=[^\\])%.*", "%", content)
    content = re.sub(r"\n([ \t]*%\n)*", "\n", content)
    content = re.sub(r"(?<=\~)\%\n", "", content, flags=re.DOTALL)

    content = re.sub(r"\\allowbreak", "", content, flags=re.DOTALL)

    # polecenia z prepare_articles - usuwanie wstępne
    content = re.sub(r"\\includeonly\{[^\}]*\}", "", content)
    content = re.sub(r"\\input\{[^\}]*\}", "", content)
    content = re.sub(r"\\input\ ?[^\\\ ]*", "", content)

    # usuwa zbędne puste linie i zostawia maksymalnie 2 puste linie
    content = re.sub(r"\n\n\n+", r"\n\n", content)

    return content
