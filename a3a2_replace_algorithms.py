import re
from config import PATH, FILE


def replace_algorithms(content: str) -> str:

    i = 1
    algorithms = re.findall(
        r"(\\begin\{algorithm\}.*?\\end\{algorithm\})", content, flags=re.DOTALL
    )
    algorithms2 = re.findall(
        r"(\\begin\{algorithmic\}.*?\\end\{algorithmic\})", content, flags=re.DOTALL
    )
    img_src = str(PATH.FIGURES) + "/" + FILE().source.tex.stem + "-algorithm-"
    for algorithm in algorithms + algorithms2:
        algorithm_file = img_src + str(i) + ".png"
        content = content.replace(
            algorithm, "\\includegraphics{" + algorithm_file + "}"
        )
        print("- ALG: zamienilem algorytm na \\includegraphics{" + algorithm_file + "}")
        print("- ALG: UWAGA! trzeba stworzyć " + algorithm_file)
        i = i + 1
    return content
