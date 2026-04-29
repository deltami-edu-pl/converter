import re
import subprocess
from pathlib import Path
from config import PATH


# \includegraphics[opts]{path} - opts moga zawierac trim/clip/scale itp.
INCL_RE = re.compile(r"\\includegraphics\[([^\]]*)\]\{([^}]+)\}")
TRIM_RE = re.compile(
    r"trim\s*=\s*([\-0-9.]+)\s+([\-0-9.]+)\s+([\-0-9.]+)\s+([\-0-9.]+)"
)


def crop_trim_images(content: str) -> str:
    """
    Pandoc emituje gole <img/> i ignoruje trim/clip - wiec po jego stronie
    przycinanie znika. Tutaj fizycznie przycinamy plik PNG ImageMagickiem
    i przepisujemy \\includegraphics na nowa sciezke bez trim/clip.

    Konwencja: bp -> px wedlug DPI obrazka (PNG ma metadana rozdzielczosc).
    Trim w LaTeX to "left bottom right top" w jednostkach bp (1bp = 1/72 cala).
    """

    def replace(match: re.Match) -> str:
        opts = match.group(1)
        path = match.group(2)

        if "clip" not in opts:
            return match.group(0)
        trim_match = TRIM_RE.search(opts)
        if trim_match is None:
            return match.group(0)

        L_bp, B_bp, R_bp, T_bp = (float(x) for x in trim_match.groups())

        src = Path(path)
        if not src.is_absolute():
            src = PATH.ROOT / path
        if not src.exists():
            print(f"# WARNING: crop_trim: nie ma pliku {src}")
            return match.group(0)

        try:
            out = subprocess.run(
                ["magick", "identify", "-format", "%x %y %w %h", str(src)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip().split()
            dpi_x, dpi_y, w, h = map(float, out)
        except Exception as e:
            print(f"# WARNING: crop_trim: identify nieudane dla {src}: {e}")
            return match.group(0)

        px_l = round(L_bp * dpi_x / 72)
        px_b = round(B_bp * dpi_y / 72)
        px_r = round(R_bp * dpi_x / 72)
        px_t = round(T_bp * dpi_y / 72)
        crop_w = int(w - px_l - px_r)
        crop_h = int(h - px_t - px_b)
        if crop_w <= 0 or crop_h <= 0:
            print(f"# WARNING: crop_trim: niepoprawne wymiary po cropie {src}")
            return match.group(0)

        cropped = src.with_stem(src.stem + "-cropped")
        if not cropped.exists():
            try:
                subprocess.run(
                    [
                        "magick", str(src),
                        "-crop", f"{crop_w}x{crop_h}+{px_l}+{px_t}",
                        "+repage",
                        str(cropped),
                    ],
                    check=True,
                    capture_output=True,
                )
                print(f"# Cropped {src.name} -> {cropped.name}")
            except subprocess.CalledProcessError as e:
                print(f"# WARNING: crop_trim: magick nieudany dla {src}: {e}")
                return match.group(0)

        # zdejmij trim/clip z opcji
        new_opts = TRIM_RE.sub("", opts)
        new_opts = re.sub(r"\bclip\b", "", new_opts)
        new_opts = re.sub(r",\s*,", ",", new_opts).strip(", \t")

        # podmien sciezke pliku
        new_path = path.replace(src.name, cropped.name)

        if new_opts:
            return f"\\includegraphics[{new_opts}]{{{new_path}}}"
        return f"\\includegraphics{{{new_path}}}"

    return INCL_RE.sub(replace, content)
