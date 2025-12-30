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
