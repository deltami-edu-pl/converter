import re
from pathlib import Path
from wand.image import Image


def contain_tikz(content: str) -> bool:
    return len(re.findall(r"\\begin\{tikzpicture\}", content)) > 0


def convert_pdf_to_png(pdf_file: Path, dest_path: Path) -> bool:
    try:
        with Image(filename=str(pdf_file), resolution=600) as img:
            img.format = "png"
            img.alpha_channel = "remove"
            img.background_color = "white"
            img.compression_quality = 100
            img.save(filename=str(dest_path))
        return True
    except Exception as e:
        print(f"# ERROR: Converting PDF to PNG: {pdf_file.name} -> {dest_path}")
        print(f"    {e}")
        return False


def wrap_overlay_centerlines(content: str) -> str:
    r"""
    Owija \centerline{...} ktore zawiera \includegraphics RAZEM z \llap (czyli
    autor naklada napisy na obrazek przez raise/llap/kern) wewnatrz
    tikzpicture+node. Dzieki temu:
      - pdflatex (a2) widzi to jako tikzpicture i renderuje do PDF -> PNG z
        napisami spalonymi na obrazku,
      - pandoc (a3) podmienia tikzpicture na <img> z gotowym, zlozonym PNG
        zamiast zubozalym goly \includegraphics (bo pandoc gubi llap/raise).
    Idempotentne: pomija centerline ktore juz ma \begin{tikzpicture} w srodku.
    """
    result = []
    i = 0
    needle = r"\centerline{"
    while i < len(content):
        idx = content.find(needle, i)
        if idx == -1:
            result.append(content[i:])
            break
        result.append(content[i:idx])
        depth = 1
        j = idx + len(needle)
        while j < len(content) and depth > 0:
            if content[j] == "{":
                depth += 1
            elif content[j] == "}":
                depth -= 1
            j += 1
        if depth != 0:
            result.append(content[idx:])
            break
        inner = content[idx + len(needle) : j - 1]
        if (
            r"\includegraphics" in inner
            and r"\llap" in inner
            and r"\begin{tikzpicture}" not in inner
        ):
            result.append(
                r"\centerline{\begin{tikzpicture}\node[inner sep=0pt,inner xsep=2cm]{"
                + inner
                + r"};\end{tikzpicture}}"
            )
        else:
            result.append(content[idx:j])
        i = j
    return "".join(result)


def log_section(func):
    def wrapper(*args, **kwargs):
        name = func.__name__
        print()
        print(f"### {name}")
        result = func(*args, **kwargs)
        print()
        print(f"### {name} done")
        return result

    return wrapper
