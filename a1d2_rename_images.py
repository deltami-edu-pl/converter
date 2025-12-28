import re
import sys
import os
from config import VERSION, PATH_SOURCE, PATH_FIGURES, PATH_DELTA_TEX, log_section

used_names = []


def crop_image(figures_folder: str, name: str, params: str) -> str | None:
    name_noext = re.sub(r"\.[a-zA-Z0-9_]+$", "", name)
    new = name

    if not os.path.exists(figures_folder + "/" + name):
        print("!! Figure " + name + " does not exist.")

    trim_match = re.match(r"^\[trim=\{?([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)\}?,", params)
    if not trim_match:
        return ""
    print("- I am trimming figure " + name)

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
        + figures_folder
        + "/"
        + name
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


def rename_images(content: str) -> str | None:
    figures_folder = str(PATH_FIGURES)  # 2025-figures

    # zamiana sciezek - wszystkie obrazki sa w figures/ oraz pdfy zostaly przerobione na png i sa includowane teraz
    matches = re.findall(
        r"(\\includegraphics(\[[^\]]*\])?\%?\s*?\{([^\}]*)\})", content, re.DOTALL
    )
    matches2 = re.findall(r"(\\img(\[[^\]]*\])?\{([^\}]*)\})", content, re.DOTALL)
    matches = matches + matches2
    extensions = ["png", "jpg", "jpeg", "PNG", "JPG", "JPEG"]

    for match in matches:
        match_all = os.path.basename(match[2])
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
