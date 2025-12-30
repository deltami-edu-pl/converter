import re
import os
import subprocess
from config import PATH, FILE
from helper import contain_tikz


# zamienia tikzpicture na \includegraphics{imagepath_noext.png}, gdzie obrazek jest przekonwertowany z xxx.pdf
def replace_images(content: str) -> str:
    if contain_tikz(content):
        # zamiana tikzpicture na includegraphics
        i = 0
        matches = re.findall(
            r"(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})", content, flags=re.DOTALL
        )
        for match in matches:
            image_path = PATH.FIGURES / (FILE().images.tex.stem + "-figure" + str(i))
            content = replace_tikz(content, match, str(image_path))
            i = i + 1

        content = re.sub(
            r"\\usepackage\{tikz\}\n\\usetikzlibrary\{external\}\n\\tikzexternalize\[shell escape=-enable-write18, prefix=[^\]]*\]\n\\tikzset\{external/force remake\}\n\\tikzset\{/pgf/images/external info\}\n\\tikzexternalize",
            "\\\\usepackage{tikz}",
            content,
        )
    return content

    # filename_tikz_after = filename_noext+"-"+IMAGES_AFTER+".tex"
    # with open(filename_tikz_after, 'w') as file:
    #     file.write(content)
    #


def replace_tikz(content, match, imagepath_noext):
    metadata_file = imagepath_noext + ".dpth"
    imagepdf_file = imagepath_noext + ".pdf"
    image_file = imagepath_noext + ".png"

    print("- TikZ: podmieniam na \\includegraphics{" + image_file + "}")

    widthtext = ""
    if os.path.isfile(imagepdf_file):
        convert_call_string = (
            'magick -density 600 "'
            + imagepdf_file
            + '" -transparent white -colorspace sRGB -limit memory 64MB -limit map 128MP "'
            + image_file
            + '"'
        )
        result = subprocess.run(
            convert_call_string, shell=True, check=False, capture_output=True
        )
        if result.stderr:
            print("-- ! error: TikZ: konwersja nieudana " + str(result.stderr))
        else:
            if not os.path.isfile(image_file):
                print("-- ! error: TikZ: konwersja nieudana " + convert_call_string)

        if os.path.isfile(metadata_file):
            with open(metadata_file, "r") as file:
                metadata = file.read()
            for width_all in re.findall(
                r"\\pgfexternalwidth\ \{([0-9]+)pt\.", metadata
            ):
                widthtext = "[width=" + width_all[0] + "pt]"

    if not os.path.isfile(image_file):
        print(
            "-- ! TikZ: error: nie ma obrazka "
            + image_file
            + "! sprawdz bledy w kompilowaniu lub wgraj obrazek o tej nazwie"
        )

    return content.replace(
        match, "\\includegraphics" + widthtext + "{" + image_file + "}"
    )
