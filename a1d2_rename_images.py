import re
import os
from config import PATH

used_names = []


def find_crop_source(figures_folder: str, name: str) -> str | None:
    """
    Sciezka do zrodla dla cropu. PDF-y sa w figures/ tylko jako przekonwertowane
    PNG (prepare_images), wiec oryginal trzeba wziac z got/ - crop liczy offsety
    wzgledem PDF-a renderowanego w 720 dpi, na PNG-u wyszlyby przesuniete.
    """
    in_figures = figures_folder + "/" + name
    if os.path.exists(in_figures):
        return in_figures

    source = next(PATH.SOURCE.rglob(name), None)
    if source is not None:
        return str(source)

    return None


def crop_image(figures_folder: str, name: str, params: str) -> str | None:
    name_noext = re.sub(r"\.[a-zA-Z0-9_]+$", "", name)
    new = name

    source = find_crop_source(figures_folder, name)
    if source is None:
        print("!! Figure " + name + " does not exist.")

    trim_match = re.match(r"^\[trim=\{?([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)\}?,", params)
    if not trim_match:
        return ""
    if source is None:
        print("!! Cannot trim " + name + " - no source file found.")
        return ""
    print("- I am trimming figure " + name + " (from " + source + ")")

    j = 1
    while name_noext + "-crop-" + str(j) + ".png" in used_names:
        j = j + 1
    new_pdf = name_noext + "-crop-" + str(j) + ".pdf"
    new = name_noext + "-crop-" + str(j) + ".png"

    os.system(
        "convert -crop +"
        + trim_match[1]
        + "0+"
        + trim_match[4]
        + "0 -crop -"
        + trim_match[3]
        + "0-"
        + trim_match[2]
        + "0 -density 720x720 +repage "
        + source
        + " "
        + figures_folder
        + "/"
        + new_pdf
    )
    os.system(
        "convert -density 600 -transparent white -colorspace sRGB -limit memory 64MB -limit map 128MB "
        + figures_folder
        + "/"
        + new_pdf
        + " "
        + figures_folder
        + "/"
        + new
    )

    used_names.append(new)
    return new


def simple_defs() -> dict[str, str]:
    r"""
    Bezargumentowe \def\name{prosta-wartosc} z glownego pliku numeru
    (got/YYYY-NN-delta.tex) - w praktyce \def\nr{08}. Nazwy plikow w
    artykulach sa skladane z tych makr (\includegraphics{logo-tjz-\nr}),
    a rename_images dziala na surowym tekscie i makra nie rozwinie -
    sciezka trafia do pandoca jako "logo-tjz-\nr" i konczy jako "logo-tjz-".
    Bierzemy tylko wartosci bez makr i klamerek, zeby nie ruszac makr
    formatujacych.
    """
    main_tex = PATH.DELTA.read_text(encoding="utf-8")
    return {
        name: value
        for name, value in re.findall(
            r"\\def\\([a-zA-Z]+)\{([A-Za-z0-9._-]*)\}", main_tex
        )
    }


def expand_defs(path: str, defs: dict[str, str]) -> str:
    r"""Rozwija \name z defs w sciezce do pliku. \nr nie moze zjesc \nrx."""
    def repl(m: re.Match) -> str:
        return defs.get(m.group(1), m.group(0))

    return re.sub(r"\\([a-zA-Z]+)", repl, path)


def rename_images(content: str) -> str | None:
    figures_folder = str(PATH.FIGURES)  # 2025-figures
    defs = simple_defs()

    # zamiana sciezek - wszystkie obrazki sa w figures/ oraz pdfy zostaly przerobione na png i sa includowane teraz
    matches = re.findall(
        r"(\\includegraphics(\[[^\]]*\])?\%?\s*?\{([^\}]*)\})", content, re.DOTALL
    )
    matches2 = re.findall(r"(\\img(\[[^\]]*\])?\{([^\}]*)\})", content, re.DOTALL)
    matches = matches + matches2
    extensions = ["png", "jpg", "jpeg", "PNG", "JPG", "JPEG"]

    for match in matches:
        match_all = os.path.basename(expand_defs(match[2], defs))
        match_noext = re.sub(r"\.[a-zA-Z0-9_]+$", "", match_all)
        match_ext = re.search(r"\.([a-zA-Z0-9_]+)$", match_all)
        new = match_all
        params = match[1]

        if match_ext:
            if match_ext.group(1) == "pdf":
                new = match_noext + ".png"

                maybe_new_name = crop_image(figures_folder, match_all, params)
                if not maybe_new_name == "":
                    new = maybe_new_name
                    params = re.sub(
                        r"^\[trim=\{?([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)\}?,",
                        "[",
                        params,
                    )

            if match_ext.group(1) == "eps":
                new = match_noext + "-eps-converted-to.png"
        else:
            if os.path.exists(figures_folder + "/" + match_noext + ".pdf"):
                new = match_noext + ".png"
                maybe_new_name = crop_image(
                    figures_folder, match_noext + ".pdf", params
                )
                if not maybe_new_name == "":
                    new = maybe_new_name
                    params = re.sub(
                        r"^\[trim=\{?([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)\}?,clip,",
                        "[",
                        params,
                    )
                    params = re.sub(
                        r"^\[trim=\{?([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)\}?(,clip)?,",
                        "[",
                        params,
                    )
            else:
                i = 0
                while i < len(extensions) and not os.path.exists(
                    figures_folder + "/" + match_noext + "." + extensions[i]
                ):
                    i = i + 1
                if i < len(extensions):
                    new = match_noext + "." + extensions[i]
                else:
                    if os.path.exists(figures_folder + "/" + match_noext + ".eps"):
                        match_noext = match_noext + "-eps-converted-to"
                    i = 0
                    while i < len(extensions) and not os.path.exists(
                        figures_folder + "/" + match_noext + "." + extensions[i]
                    ):
                        i = i + 1
                    if i < len(extensions):
                        new = match_noext + "." + extensions[i]

        if not os.path.exists(figures_folder + "/" + new):
            print("Figure " + new + " does not exist.")

        content = content.replace(
            match[0],
            "\\includegraphics" + params + "{" + figures_folder + "/" + new + "}",
        )

    return content
