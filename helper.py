import functools
import re
import shlex
import shutil
import subprocess
import tempfile
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


def convert_mps_to_png(mps_file: Path, dest_path: Path) -> bool:
    """
    MetaPost (.mps) -> PNG, przez mptopdf.

    Ghostscript sam tego nie otworzy: .mps to PostScript, ktory odwoluje sie do
    fontow TeX-owych po nazwie (cmbx10) i ich nie osadza - magick konczy na
    "/undefined in cmbx10". mptopdf ma dostep do fontow TeX Live i osadza je w
    PDF-ie, ktory dalej idzie zwykla sciezka PDF->PNG.

    mptopdf zapisuje wynik OBOK pliku wejsciowego, a wejscie lezy w got/ -
    nietykalnym dropie redakcji. Dlatego kopiujemy .mps do katalogu tymczasowego
    i konwertujemy tam.
    """
    if not shutil.which("mptopdf"):
        print(f"# ERROR: brak mptopdf w PATH - nie przekonwertuje {mps_file.name}")
        return False

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        local_mps = tmp_path / mps_file.name
        shutil.copy2(mps_file, local_mps)
        # przez powloke swiadomie: mptopdf to skrypt Perla BEZ shebanga -
        # zaczyna sie od "eval 'exec perl -S $0'", ktore dziala tylko gdy
        # uruchomi go /bin/sh. Exec wprost konczy sie "Exec format error".
        result = subprocess.run(
            f"mptopdf {shlex.quote(local_mps.name)}",
            shell=True,
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        # mptopdf nazywa wynik <stem>-mps.pdf, ale wersje sie roznily - bierzemy
        # to, co faktycznie powstalo.
        pdfs = sorted(tmp_path.glob("*.pdf"))
        if not pdfs:
            print(f"# ERROR: mptopdf nie zrobil PDF-a z {mps_file.name}")
            print(f"    {result.stdout.decode(errors='replace')[-300:]}")
            return False
        return convert_pdf_to_png(pdfs[0], dest_path)


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
    # functools.wraps, zeby dekorator nie gubil nazwy, docstringa i sygnatury -
    # bez tego inspect.signature widzi (*args, **kwargs) i nie da sie
    # sprawdzic testem, ze `apply` domyslnie jest False.
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        name = func.__name__
        print()
        print(f"### {name}")
        result = func(*args, **kwargs)
        print()
        print(f"### {name} done")
        return result

    return wrapper
