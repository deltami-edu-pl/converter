import unicodedata
import re
import os
import requests
import urllib.error
import sys
import urllib.parse
from bs4 import BeautifulSoup
from bs4 import Comment
from urllib.parse import urljoin, urlparse
from urllib.request import urlretrieve
import subprocess
from config import VERSION, GET_NEXT_TEX_FILE, log_section
from pathlib import Path

FILENAME_ADD_TIKZ = "tikz"
FILENAME_ADD_PANDOC = "pandoc"

NEWPAGE = 'convert.html'

TEXTWIDTH = 356 # 356 pt - szerokosc strony (\textwidth) w formacie Delty; uzywane aby poprawiac szerokosc obrazkow
COLOR = 'FF0088'

##############################################
############ MAIN FUNCTION ###################
##############################################

@log_section
def convert_to_html():
    # if len(sys.argv) < 3:
    #     print("Za mało parametrów: python xxxxx.py <figures_folder> <filename>")
    #     sys.exit(1)

    figures_folder = f"{VERSION}-figures"
    filename = GET_NEXT_TEX_FILE()

    if figures_folder[-1] == "/": 
        figures_folder = figures_folder[:-1]
        
    filename_noext = re.sub(r'\.[a-z]+$', '', filename)

    if not os.path.isfile(filename):
        print(f"Plik {filename} nie istnieje.")
        sys.exit(1)

    with open(filename, 'r') as file:
        content = file.read()

    # usuniecie komentarzy
    print("- usuwam komentarze")
    content = remove_comments(content)

    # usuniecie zadan i rozwiazan
    print("- usuwam zadania i rozwiązania")
    content = re.sub(r'\\zadMat\{[0-9]+\}', '',content)
    content = re.sub(r'\\zadFiz\{[0-9]+\}', '',content)
    content = re.sub(r'\\rozMat(\[[0-9\-]+\])?\{[0-9]+\}', '',content)
    content = re.sub(r'\\rozFiz(\[[0-9\-]+\])?\{[0-9]+\}', '',content)
    content = re.sub(r'\\szrozFiz\{[0-9]+\}', '',content)
    
    # usuniecie input
    content = re.sub(r'\\input\s+[^\s]+\s', ' ',content)
    content = re.sub(r'\\input\s+[^\\]+\\', '\\\\',content)

    # podstawienie '\def{\rysa} w miejsce pojawienia aby byla dobra kolejnosc
    matches  = re.findall(r'(\\def(\\rys[^\{]*)\{(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})\})',content, flags=re.DOTALL)
    matches2 = re.findall(r'(\\def(\\rys[^\{]*)\{(\\scalebox\{[^\}]*\}\{\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})\}\})',content, flags=re.DOTALL)
    if len(matches+matches2) > 0:
        print("- podmieniam komendy \\def\\rysx")
    
    for match in sorted(matches+matches2, key=lambda x: -len(x[1])):
        content = content.replace(match[0],'')
        content = content.replace(match[1], match[2])
        
    content = re.sub(r"\\allowbreak", "", content, flags=re.DOTALL)

    # zamiana \ref na \eqref i usunięcie okalających nawiasów
    content = re.sub(r"\(\\ref\{([a-zA-Z0-9_]+)\}\)", r"\\eqref{\1}", content, flags=re.DOTALL)

    # zamiana \leqno(1) na \tag{1}
    content = re.sub(r"\\leqno\(([^)]+)\)", r"\\tag{\1}", content, flags=re.DOTALL)    

    # specjalne formuly dla pliku z zadaniami
    if re.findall(r'\\zadanieM', content):
        newcommands = "\\theoremstyle{definition}\\newtheorem{exercise}{Zadanie}\n\\newtheorem{answer}{Rozwiązanie}\n\n"
        newcommands = newcommands + "\\renewcommand{\\zadanieM}[3]{\\begin{exercise}{M #1.}#2\\begin{answer}#3\\end{answer}\\end{exercise}}\n"
        newcommands = newcommands + "\\renewcommand{\\zadanieF}[3]{\\begin{exercise}{F #1.}#2\\begin{answer}#3\\end{answer}\\end{exercise}}\n"
        content = content.replace('\\begin{document}', newcommands+'\n\\begin{document}\\title{Zadania}')
    
    content = re.sub(r'\\angle', r'\\measuredangle', content)
    
    # ustawienie koloru
    content = content.replace("\\begin{document}", "\\definecolor{deltaColor}{HTML}{"+COLOR+"}\n\\colorlet{magenta}{deltaColor}\n\n\\begin{document}")
    
    # dodanie \usetkzobjc{all}, bo czesto sie nie kompiluje bez oraz ustawienie eksportowania obrazkow
    if len(re.findall(r'\\begin\{tikzpicture\}', content)) > 0:
        print("- TikZ: ustawiam eksportowanie obrazkow do katalogu "+figures_folder)
        # content = re.sub(r'\\usepackage\{tkz-euclide\}', '\\\\usepackage{tkz-euclide}\n\\\\usetkzobj{all}',content)
        content = re.sub(r'\\usepackage\{tikz\}', '\\\\usepackage{tikz}\n\\\\usetikzlibrary{external}\n\\\\tikzexternalize[shell escape=-enable-write18, prefix='+figures_folder+'/]\n\\\\tikzset{external/force remake}\n\\\\tikzset{/pgf/images/external info}\n\\\\tikzexternalize',content)

    # TU SIĘ ZAPISUJE TIKZ
    filename_tikz = filename_noext+"-"+FILENAME_ADD_TIKZ+".tex"
    with open(filename_tikz, 'w') as file:
        file.write(content)

    if len(re.findall(r'\\begin\{tikzpicture\}', content)) > 0:
        # wywolanie pdflatex
        pdflatex_call_string = "pdflatex --shell-escape -interaction=nonstopmode -file-line-error \""+filename_tikz+"\""
        print("- TikZ: " + pdflatex_call_string)
        result = subprocess.run(pdflatex_call_string, shell=True, check=False, capture_output=True)
        if result.returncode != 0:
            print("! TikZ: error: pdflatex zwrócił błąd")
        else:    
            print("- TikZ: sukces!")

        # zamiana tikzpicture na includegraphics
        i=0
        matches = re.findall(r'(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})', content, flags=re.DOTALL)
        for match in matches:
            content = replace_tikz(content, match, figures_folder+"/"+filename_noext+"-"+FILENAME_ADD_TIKZ+"-figure"+str(i))
            i=i+1

    content = re.sub(r'\\usepackage\{tikz\}\n\\usetikzlibrary\{external\}\n\\tikzexternalize\[shell escape=-enable-write18, prefix=[^\]]*\]\n\\tikzset\{external/force remake\}\n\\tikzset\{/pgf/images/external info\}\n\\tikzexternalize','\\\\usepackage{tikz}',content)

    # filename_tikz_after = filename_noext+"-"+FILENAME_ADD_TIKZ_AFTER+".tex"
    # with open(filename_tikz_after, 'w') as file:
    #     file.write(content)
    #
    content = replace_algorithms(content, filename_noext, figures_folder)
    content = prepare_pandoc(content)

    # TU SIĘ ZAPISUJE PANDOC
    filename_pandoc = filename_noext+"-"+FILENAME_ADD_PANDOC+".tex"
    with open(filename_pandoc, 'w') as file:
        file.write(content)

    filename_pandoc_after = filename_noext+"-"+FILENAME_ADD_PANDOC+".html"
    pandoc_call_string = "pandoc --wrap=preserve "+filename_pandoc+" -t html -V lang=pl --mathjax -s -o "+filename_pandoc_after+" --citeproc"
    print("- Pandoc: " + pandoc_call_string)
    result = subprocess.run(pandoc_call_string, shell=True, check=False, capture_output=True)
    if result.stderr:
        print("! Pandoc: error: pandoc zwrócił błąd")
        print(result.stderr)

    filename_pandoc_after = filename_noext+"-"+FILENAME_ADD_PANDOC+".html"

    if not os.path.isfile(filename_pandoc_after):
        print(f"! Pandoc: plik "+filename_pandoc_after+" nie istnieje")
        print(f"! END: niestety nie udalo sie stworzyc htmla")
        sys.exit(1)
    print(f"- Pandoc: sukces! aby sprawdzic ostrzezenia uruchom komende:")
    print(pandoc_call_string+" --verbose")

    with open(filename_pandoc_after, 'r') as file:
        html_content = file.read()

    newsoup = correct_html(html_content)

    html_filename = filename_noext+".html"
    html_final_content = re.sub(r"\n\n\n+", r"\n\n", str(newsoup))
    # html_final_content = newsoup.encode('utf-8')
    with open(html_filename, 'wb') as file:
        file.write(html_final_content.encode('utf-8'))

    print(f"- SUKCES! plik "+html_filename+" stworzony!")

    # USUWAM WSZYSTKIE PLIKI TYMCZASOWE
    # os.remove(filename_pandoc_after)

##############################################
############ OTHER FUNCTIONS #################
##############################################

# usuwa zawartosc komentarzy oraz linie, w ktorych sa tylko komentarze
def remove_comments(content):
    content = re.sub(r'(?<=[^\\])%.*', '%', content)
    content = re.sub(r'\n([ \t]*%\n)*','\n', content) 
    content = re.sub(r'(?<=\~)\%\n','', content, flags=re.DOTALL)
    
    return content
    
def add_links_to_delta(soup):
    span_maths = soup.find_all("span", "math")
    for span in span_maths:
        if span.find_parent("a") is None:
            month = ""
            match = re.match(r'\\\(\\Delta\_\{([0-9]+)\}\^\{([0-9]+)\}', span.text)
            if not match:
                match = re.match(r'\\\(\\Delta\_\{([0-9]+)\}\^([0-9])', span.text)
            if match:
                year = match[1]
                month = match[2]
                    
            match = re.match(r'\\\(\\Delta\^\{([0-9]+)\}\_\{([0-9]+)\}', span.text)
            if not match:
                match = re.match(r'\\\(\\Delta\^([0-9])\_\{([0-9]+)\}', span.text)
            if match:
                year = match[2]
                month = match[1]
                
            if not month == "":
                if int(year) < 74:
                    year = "20"+year
                else:
                    year = "19"+year
                if int(month) < 10:
                    month = "0"+str(int(month))
                a_tag = soup.new_tag("a")
                a_tag['href'] = "https://deltami.edu.pl/"+year+"/"+month+"/"
                span.replace_with(a_tag)
                a_tag.append(span)
                print("- dodałem link: "+a_tag['href']+" do "+span.text+" (można doprecyzować)")
    return soup

# zamienia tikzpicture na \includegraphics{imagepath_noext.png}, gdzie obrazek jest przekonwertowany z xxx.pdf
def replace_tikz(content, match, imagepath_noext):
    metadata_file = imagepath_noext + ".dpth"
    imagepdf_file = imagepath_noext + ".pdf"
    image_file = imagepath_noext + ".png"
    
    print("- TikZ: podmieniam na \\includegraphics{"+image_file+"}")
    
    widthtext = ""
    if os.path.isfile(imagepdf_file):
        convert_call_string = "magick -density 600 \""+imagepdf_file+"\" -transparent white -colorspace sRGB -limit memory 64MB -limit map 128MP \""+image_file+"\""
        result = subprocess.run(convert_call_string, shell=True, check=False, capture_output=True)
        if result.stderr:
            print("-- ! error: TikZ: konwersja nieudana " + str(result.stderr))
        else:
            if not os.path.isfile(image_file):
                print("-- ! error: TikZ: konwersja nieudana " + convert_call_string)

        if os.path.isfile(metadata_file):
            with open(metadata_file, 'r') as file:
                metadata = file.read()
            for width_all in re.findall(r'\\pgfexternalwidth\ \{([0-9]+)pt\.', metadata):
                widthtext = "[width="+width_all[0]+"pt]"
        
    if not os.path.isfile(image_file):
        print("-- ! TikZ: error: nie ma obrazka "+image_file+"! sprawdz bledy w kompilowaniu lub wgraj obrazek o tej nazwie")
    
    return(content.replace(match, "\\includegraphics"+widthtext+"{"+image_file+"}"))

def replace_algorithms(content, filename_noext, figures_folder):
    i=1
    algorithms = re.findall(r'(\\begin\{algorithm\}.*?\\end\{algorithm\})', content, flags=re.DOTALL)
    algorithms2 = re.findall(r'(\\begin\{algorithmic\}.*?\\end\{algorithmic\})', content, flags=re.DOTALL)
    for algorithm in algorithms + algorithms2:
        algorithm_file = figures_folder+"/"+filename_noext+'-algorithm-'+str(i)+'.png'
        content = content.replace(algorithm, '\\includegraphics{'+algorithm_file+'}')
        print("- ALG: zamienilem algorytm na \\includegraphics{"+algorithm_file+"}")
        print("- ALG: UWAGA! trzeba stworzyć "+algorithm_file)
        i=i+1
    return content

def prepare_pandoc(content):
    pt = "(cm|pt|px|em)"
    
    # dodaje komende, bo w ten sposob moge zmienic \marg{ na \myquote{ i nie musz szukac konca nawiasu aby wstawic \end{quote}
    content = re.sub(r'\\begin\{document\}', '\\\\newcommand{\\\\myquote}[1]{\\\\footnote{\\\\begin{quote}#1\\\\end{quote}}}\n\n\\\\begin{document}', content)
    
    matches  = re.findall(r'(\\rlap\{(\$\\Delta[^\$]*\$)\}\\href\{([^\}]+)\}\{[^\}]+\})', content, flags=re.DOTALL)
    for match in matches:
        content = content.replace(match[0], "\\href{"+match[2]+"}{"+match[1]+"}")
    
    matches  = re.findall(r'(\\href\{([^\}]+)\}\{[^\}]+\}\\llap\{(\$\\Delta[^\$]*\$)\})', content, flags=re.DOTALL)
    for match in matches:
        content = content.replace(match[0], "\\href{"+match[1]+"}{"+match[2]+"}")
    
    content = re.sub(r'\n\\okladka(\[[0-9\-]*\])?\n','\n', content) # 2023-12 only
    content = re.sub(r'\{\\color\{red\}','\\\\textcolor{red}{', content)

    content = re.sub(r'\\includegraphics\[[^\]]*\]\{[^\}]*kmo_logo_krzywe.png\}', '', content)
    
    content = re.sub(r'\\wd0', '0', content)
    content = re.sub(r'\\hangindent[0-9]+'+pt, '', content)
    content = re.sub(r'\\hangindent[0-9]+', '', content)
    content = re.sub(r'\\hangafter[0-9]+', '', content)
    content = re.sub(r'\\lower[0-9\.]+'+pt, '', content)
    content = re.sub(r'\\phantom1', '', content)
    content = re.sub(r'\\scalebox\{[^\}]*\}', '', content)

    content = re.sub(r'\\hsize[0-9\.]+'+pt, '', content)
    content = re.sub(r'\\noindent', '', content)
    content = re.sub(r'\\vtop', '', content)
    content = re.sub(r'\\begin\{thebibliography\}\{[A-Za-z0-9\-]*\}','\\\\begin{bibliography}', content)
    content = re.sub(r'\\end\{thebibliography\}','\\\\end{bibliography}', content)
        
    if re.findall(r'\\long\\def\\matematyka', content):
        content = content.replace('\\begin{document}', '\\begin{document}\\title{Klub 44}')
    
    content = re.sub(r'\\img\[[^\]]*\]\{klub44-[^\}]*\}', '', content)
    content = re.sub(r'\\long\\def\\matematyka', '', content)
    content = re.sub(r'\\long\\def\\fizyka', '', content)
    content = re.sub(r'\\matematyka', '', content)
    content = re.sub(r'\\fizyka', '', content)
    content = re.sub(r'\\klub\[[0-9]*\]\{(m|f)\}', '', content)
    
    if re.findall(r'\\def\\pp\(\#\#1\) \{\&\#\#1\&\}', content):
        content = re.sub(r'\\def\\pp\(\#\#1\) \{\&\#\#1\&\}', '', content)
        content = re.sub(r'\\pp\(([^\)]*)\)', r'& \1 &', content)

    # usunięcie \textsc
    content = re.sub(r'\\textsc','', content)
    # zamiana \mathbbm na \mathbb
    content = content.replace('\\mathbbm','\\mathbb')

    # usuniecie vspace, newpage
    content = re.sub(r'\\smallskip','', content)
    content = re.sub(r'\\medskip','', content)
    content = re.sub(r'\\vspace\{[^\}]*\}','', content)
    content = re.sub(r'\\vspace\*\{[^\}]*\}','', content)
    content = re.sub(r'\\hspace\{[^\}]*\}','', content)
    content = re.sub(r'\\hspace\*\{[^\}]*\}','', content)
    content = re.sub(r'\\hfill','', content)
    content = re.sub(r'\\quad\{', '{', content)
    content = re.sub(r'\\newpage','', content)
    content = re.sub(r'\\break','', content)
    content = re.sub(r'\\nobreak','', content)
    content = re.sub(r'\\fboxsep[0-9\.-]*'+pt, '', content)
    content = re.sub(r'\\rotatebox\{90\}', '', content)
    content = re.sub(r'\\raise[0-9\.-]*'+pt, '', content)
    content = re.sub(r'\\rightskip\sby[0-9\.-]*'+pt, '', content)
    content = re.sub(r'\\slash', '/', content)
    
    if re.findall(r'\\fbox', content):
        content = re.sub(r'\\begin\{document\}', '\\\\renewcommand{\\\\fbox}[1]{\\\\begin{framed}#1\\\\end{framed}}\n\\\\begin{document}', content)
      
    theorems = {"fakt": "Fakt", "wniosek": "Wniosek", "przypuszczenie": "Przypuszczenie", "hipoteza": "Hipoteza", "aksjomat": "Aksjomat", "problem": "Problem", "pytanie": "Pytanie", "przyklad": "Przykład", "cwiczenie": "Ćwiczenie", "example": "Przykład", "przyklad": "Przykład", "przypadek": "Przypadek", "stwierdzenie": "Stwierdzenie", "definicja": "Definicja", "zadanie": "Zadanie", "rozwiazanie": "Rozwiązanie", "hint": "Wskazówka", "zagadka": "Zagadka", "wlasnosc": "Własność", "uwaga": "Uwaga", "sangaku": "Sangaku", "postulat": "Postulat", "eksperyment": "Ekspretyment", "solution": "rozwiazanie", "sposob": "Sposób", "twierdzenie": "Twierdzenie"}

    for key in theorems:
        name = theorems[key]
        if re.findall(r'\\begin\{'+key+r'\*?\}', content):
            content = content.replace('\\begin{document}', '\\newtheorem{'+key+'}{'+name+'}\n\\newtheorem{'+key+'*}{'+name+'}\n\n\\begin{document}')
            content = re.sub(r'(\\begin\{'+key+r'\*?\}(\s*\[[^\]]*\])?)', r'\1{\\em', content)
            content = re.sub(r'(\\end\{'+key+r'\*?\})', r'}\1', content)
    
    content = re.sub(r'\\spis\{[^\}]*\}\s*\{[^\}]*\}','', content, flags=re.DOTALL)
    content = re.sub(r'\\kpospis\{[^\}]*\}\s*\{[^\}]*\}','', content, flags=re.DOTALL)
    content = re.sub(r'\\tikzstyle\{[^\}]*\}=\[[^\]\[]*\[[^\]]*\][^\]]*\]','', content, flags=re.DOTALL)
    content = re.sub(r'\\tikzstyle\{[^\}]*\}=\[[^\]]*\]','', content, flags=re.DOTALL)
    content = re.sub(r'\\aafil(\[[^\]]*\])?\{', '\\\\marg{Afiliacja: ', content)
    content = re.sub(r'\\resizebox\{[^\}]*\}\{[^\}]*\}','', content, flags=re.DOTALL)
    content = re.sub(r'(\\color\{[a-zA-Z0-9]+\})([^{]*?)(?=})', r'\1{\2}', content)
    content = re.sub(r'\\color\{magenta\}', '\\\\textcolor{deltaColor}', content)
    content = re.sub(r'\\Magenta\s?\{', '\\\\textcolor{deltaColor}{ ', content)
    content = re.sub(r'\\llap', '', content)
    content = re.sub(r'\\vskip\\parskip', '', content)
    content = re.sub(r'\\looseness-[0-9]+', '', content)
    content = re.sub(r'\\arraycolsep\.[0-9]+'+pt, '', content)
    content = re.sub(r'\\quad', '\\\\ \\\\ \\\\ ', content)
    content = re.sub(r'\\qquad', '\\\\ \\\\ \\\\ ', content)
    content = re.sub(r'\\begin\{multicols\}\{[0-9]+\}', '', content)
    content = re.sub(r'\\begin\{multicols\}[0-9]+', '', content)
    content = re.sub(r'\\end\{multicols\}', '', content)
    content = re.sub(r'\\setcounter\{equation\}[0-9]+', '', content)
    content = re.sub(r'\\szero[0-9\.]*'+pt, '', content)
    content = re.sub(r'\\spaceskip[0-9\.]+'+pt+r' minus[0-9\.]+'+pt+r'?', '', content)
    content = re.sub(r'\\spaceskip[0-9\.-]+'+pt, '', content)
    content = re.sub(r'\\tabcolsep\sby[0-9\-\.]+'+pt, '', content)
    content = re.sub(r'\\tabcolsep\s*[0-9\.]*'+pt, '', content)
    content = re.sub(r'\\itemsep[0-9]+'+pt, '', content)
    content = re.sub(r'\\ensuremath', '', content)

    content = re.sub(r'(?<=[^\$\\])\$,', ',$', content)
    content = re.sub(r'(?<=[^\$\\])\$\.', '.$', content)

    content = re.sub(r'\\begin\{adjustwidth\}(\{[^\}]*\})?(\{[^\}]*\})?', '', content)
    content = re.sub(r'\\end\{adjustwidth\}', '', content)
     
    content = re.sub(r'\\centerline', '', content)

    content = re.sub(r'\\refstepcounter\{figure\}', '', content)

    if re.findall(r'\\ip\{', content):
        content = re.sub(r'\\begin\{document\}', '\\\\newcommand{\\\\ip}[2]{\\\\langle #1,#2 \\\\rangle}\n\n\\\\begin{document}', content)
    if re.findall(r'\\ip\{', content):
        content = re.sub(r'\\begin\{document\}', '\\\\newcommand{\\\\op}[2]{\\\\ket{#1}\\\\bra{#2}}\n\n\\\\begin{document}', content)

    content = re.sub(r'\\xhref{', '\\\\href{', content)
    content = re.sub(r'\\xxhref{', '\\\\href{', content)
    
    content = re.sub(r'\\textbullet\{\}', '$\\\\bullet$', content)

    content = re.sub(r'\\begin\{mdframed\}', '\\\\begin{framed}', content)
    content = re.sub(r'\\end\{mdframed\}', '\\\\end{framed}', content)
    
    # content = re.sub(r'(<!\\def)\\pp', '\\\\pp{}', content)
    content = re.sub(r'\\def\\pp\#1\ ', '\\\\def\\\\nieumiemregex#1', content) # don't ask
    content = re.sub(r'\\pp', '\\\\pp{}', content) # don't ask
    content = re.sub(r'nieumiemregex', 'pp', content) # don't ask

    content = re.sub(r'\\sb','_',content)
    content = re.sub(r'\\sp(>=[0-9])','^',content)
    
    content = re.sub(r'\\Black\{', '{', content)
    content = re.sub(r'\\vrule\s+height\s?[\.0-9]+'+pt+r'\s+width\s?[\.0-9]+'+pt+r'(\s+depth\s?[\.0-9]+'+pt+r')?','',content)
    content = re.sub(r'\\vrule\s+height\s?[\.0-9]+'+pt+r'\s+depth\s?[\.0-9]+'+pt+r'(\s+width\s?[\.0-9]+'+pt+r')?','',content)
    content = re.sub(r'\\vrule\s+width\s?[\.0-9]+'+pt+r'\s+depth\s?[\.0-9]+'+pt+r'(\s+height\s?[\.0-9]+'+pt+r')?','',content)
    content = re.sub(r'\\vrule\s+width\s?[\.0-9]+'+pt+r'\s+height\s?[\.0-9]+'+pt+r'(\s+depth\s?[\.0-9]+'+pt+r')?','',content)
    content = re.sub(r'\\vrule\s+depth\s?[\.0-9]+'+pt+r'\s+width\s?[\.0-9]+'+pt+r'(\s+height\s?[\.0-9]+'+pt+r')?','',content)
    content = re.sub(r'\\vrule\s+depth\s?[\.0-9]+'+pt+r'\s+height\s?[\.0-9]+'+pt+r'(\s+width\s?[\.0-9]+'+pt+r')?','',content)

    content = re.sub(r'\\rlap\{', '{', content)
    content = re.sub(r'\\baselineskip\s+by[0-9\.\-\s]*'+pt, '', content)
    content = re.sub(r'\\baselineskip[^\s]*\s+plus\.[^\s]*\s+minus\.[^\s]*\s+', '', content)
    content = re.sub(r'\\baselineskip[^\s]*\s+plus\.[^\s]*\s+', '', content)
    content = re.sub(r'\\baselineskip[^\s]*\s+minus\.[^\s]*\s+', '', content)
    content = re.sub(r'\\baselineskip[^\s]*\s+', '', content)
    content = re.sub(r'\\parskip\s+by[0-9\.\-\s]*'+pt, '', content)
    content = re.sub(r'\\parskip[0-9\.\-\s]*'+pt, '', content)
    content = re.sub(r'\\advance', '', content)
    content = re.sub(r'\\vadjust', '', content)
    content = re.sub(r'\\goodbreak', '', content)
    content = re.sub(r'\\vskip\s*[\-0-9\.]*'+pt+r'\s+plus[\-0-9\.]*'+pt+r'\s+minus[\-0-9\.]*'+pt, '', content)
    content = re.sub(r'\\vskip\s*[\-0-9\.]*'+pt+r'\s+plus[\-0-9\.]*'+pt, '', content)
    content = re.sub(r'\\vskip\s*[\-0-9\.]*'+pt, '', content)
    content = re.sub(r'\\hskip\s*[\-0-9\.]*'+pt, '', content)
    content = re.sub(r'\\medmuskip[\-0-9\.]*mu', '', content)
    content = re.sub(r'\\kern[0-9\.-]* to[0-9\.]'+pt, '', content)
    content = re.sub(r'\\kern[0-9\.-]*'+pt, '', content)
    content = re.sub(r'\\vbox to[0-9\.]'+pt, '', content)  
    content = re.sub(r'\\dc ', ',,', content)  
    content = re.sub(r'\\vfill', '', content)  
    content = re.sub(r'\\eject', '', content)  
    content = re.sub(r'\\null', '', content)  
    content = re.sub(r'\\endinput.*', '\\\\end{document}', content, flags=re.DOTALL)
    content = re.sub(r'\\everypar=\{[^\}]*\}', '', content)
    content = re.sub(r'(?<!\$)(\\eqref\{[^\}]+\})', r'$\1$', content)
    content = re.sub(r'\\scriptsize', '', content)
    content = re.sub(r'\\normalsize', '', content)

    content = re.sub(r'=\\newline=', r'=', content)

    i=1
    matches = re.findall(r'(\\begin\{equation\}(.*?\\label.*?\\end\{equation\}))', content, flags=re.DOTALL)
    for match in matches:
        if not "\\tag" in match[0]:
            content = content.replace(match[0], "\\begin{equation}\\tag{"+str(i)+"}"+match[1])
            i=i+1
    
    matches = re.findall(r'(\\includegraphics\[width=([0-9\.]+)(pt|cm|px|in)\])', content)
    for match in matches:
        newtext = "\\includegraphics[width="+str(int(float(match[1])*1.5))+match[2]+"]"
        content = content.replace(match[0], newtext)

    matches = re.findall(r'(\\includegraphics\[width=([0-9\.]+)\\textwidth\])', content)
    for match in matches:
        newtext = "\\includegraphics[width="+str(int(float(match[1])*TEXTWIDTH*(1.5)))+"pt]"
        content = content.replace(match[0], newtext)

    matches = re.findall(r'(\$\$\s*\{*\s*(\\includegraphics(\[[^\]]*\])?\{([^\}]*)\})\s*\}*\s*\$\$)', content, flags=re.DOTALL)
    for match in matches:
        content = content.replace(match[0], "\\begin{center}"+match[1]+"\\end{center}")

    # tikz
    content = re.sub(r'\\usetikzlibrary(\[[^\]]*\])?\{[^\}]*\}','', content, flags=re.DOTALL)
    
    # algpseudocode
    content = re.sub(r'\\usepackage\[[^\]]*\]\{algpseudocode\}', '', content)  

    content = re.sub(r'\\begin\{dwieszpalty\}', '', content)
    content = re.sub(r'\\end\{dwieszpalty\}', '', content)
    content = re.sub(r'\\begin\{szeroko\}', '', content)
    content = re.sub(r'\\end\{szeroko\}', '', content)
    content = re.sub(r'\\redaguje', '', content)
    # content = re.sub(r'\\Zadania', '', content)

    content = re.sub(r'\\marg\s*\{', '\\\\myquote{', content)
    content = re.sub(r'\\marg\[[^\]]*\]\s*\{', '\\\\myquote{', content)
    content = re.sub(r'\\marginpar\{', '\\\\myquote{', content)

    # tytuły
    if content.find("\\wtyt") == -1:
        content = re.sub(r'\\mtyt', '\\\\wtyt', content, count=1)
    content = re.sub(r'\\wtyt\{', '\\\\'+'title{', content)
        
    # autor
    author_match = re.match(r'^.*(\\waut\{(\s*\\color\{black\}\s*)?([^\}]*)\}).*$', content, flags=re.DOTALL)
    if author_match is not None:
        author = author_match.group(3)
        content = content.replace(author_match.group(1), '')
        content = content.replace("\\begin{document}", "\\begin{document}\\author{"+author+"}")
    else:
        if content.find("\\waut") == -1:
            author_matches = re.findall(r'(\\rightline{\s*\\large\s*\{\}\s*\\textit\{([^\}]*)\}\s*(\{\})*\s*\})', content, flags=re.DOTALL)
            if len(author_matches) == 0:
                author_matches = re.findall(r'(\\rightline{\s*\\large\s*\\textit\{([^\}]*)\}\s*(\{\})*[\s\%]*\})', content, flags=re.DOTALL)
            if len(author_matches) == 0:
                author_matches = re.findall(r'(\\rightline{\s*\\large\s*\\it\s*([^\\]*)\s*(\\ )*[\\a-z]*\(\{[a-z\.\@\\\s]*\}\s*\)\s*\})', content, flags=re.DOTALL)
            if len(author_matches) == 0:
                author_matches = re.findall(r'(\\rightline{\s*\\large\s*\\it\s*([^\}]*)\s*(\{\})*[\s\%]*\})', content, flags=re.DOTALL)
            if len(author_matches) == 0:
                author_matches = re.findall(r'(\\rightline{\s*\\textit\{\s*([^\}]*)\s*\}\})', content, flags=re.DOTALL)
            for author_match in author_matches:
                author = author_match[1]
                content = content.replace(author_match[0], '\\waut{'+author+'}')
                print("AUTOR: "+author)
    content = re.sub(r'\\waut\{', '\\\\author{', content)
    
    # affil weird
    content = content.replace("{\\scriptsize\\rm Uniwersytet im. A. Mickiewicza w~Poznaniu}", "\\myquote{Uniwersytet im. A. Mickiewicza w~Poznaniu}")
    
    affil_matches = re.findall(r'(\\rightline\{\s*\\scriptsize\s*([^\}]*)\s*\})', content, flags=re.DOTALL)
    if len(affil_matches) > 0:
        for affil_match in affil_matches:
            affil = affil_match[1]
            print("AFFIL: "+affil)
            content = content.replace(affil_match[0], '')
            content = content.replace("\\begin{document}", "\\begin{document}\\myquote{"+affil+"}")
    else:
        affil_matches = re.findall(r'(\{\s*\\scriptsize\s\\rightline\{([^\}]*)\}\s*\\rightline\{([^\}]*)\}\s*\\rightline\{([^\}]*)\}(\s*\\par)?\s*\})', content, flags=re.DOTALL)
        if len(affil_matches) > 0:
            for affil_match in affil_matches:
                affil = affil_match[1]+"\\\\"+affil_match[2]+"\\\\"+affil_match[3]
                print("AFFIL: "+affil)
                content = content.replace(affil_match[0], '')
                content = content.replace("\\begin{document}", "\\begin{document}\\myquote{"+affil+"}")
        else:
            affil_matches = re.findall(r'(\{\s*\\scriptsize\s\\rightline\{([^\}]*)\}\s*\\rightline\{([^\}]*)\}(\s*\\par)?\s*\})', content, flags=re.DOTALL)
            if len(affil_matches) > 0:
                for affil_match in affil_matches:
                    affil = affil_match[1]+"\\\\"+affil_match[2]
                    print("AFFIL: "+affil)
                    content = content.replace(affil_match[0], '')
                    content = content.replace("\\begin{document}", "\\begin{document}\\myquote{"+affil+"}")
            else:
                affil_matches = re.findall(r'(\{\s*\\scriptsize\s\\rightline\{([^\}]*)\}(\s*\\par)?\s*\})', content, flags=re.DOTALL)
                for affil_match in affil_matches:
                    affil = affil_match[1]
                    print("AFFIL: "+affil)
                    content = content.replace(affil_match[0], '')
                    content = content.replace("\\begin{document}", "\\begin{document}\\myquote{"+affil+"}")
    # END affil weird
    
    content = re.sub(r'\\rightline\{', '\\\\myquote{', content)

    content = re.sub(r'\\mtyt\{', '\\\\subsection*{', content)
    content = re.sub(r'\\wtyt\{', '\\\\subsection*{', content)
    content = re.sub(r'\\styt\{', '\\\\subsection*{', content)
    content = re.sub(r'\\ptyt\{', '\\\\subsection*{', content)

    content = re.sub(r'\\znztyt\{[0-9]+\}\{', '\\\\title{', content)  
    content = re.sub(r'\\tjztyt\{', '\\\\title{', content)  
    content = re.sub(r'\\pzntyt\{', '\\\\title{', content)  
    content = re.sub(r'\\niebowtyt\{', '\\\\title{', content)  
    content = re.sub(r'\\vbox', '', content)  
    content = re.sub(r'\\setbox0=', '', content)  
    content = re.sub(r'\\includegraphics(\[width=[0-9\.]+cm])?\{[^/]*/kmo_logo_krzywe-eps-converted-to.png\}', '', content)  

    content = re.sub(r'\\textcolor\{black\}\{\s*\}', '', content)
    
    if re.search(r'\\mathcode`\\,=\"013B', content) :
        content = re.sub(r'\\mathcode`\\,=\"013B', '', content)    
        content = re.sub(r'(?<!\\),', '{,}', content)       
    
    return content
    
def replace_article_in_newpage(soup, title="", author="", url=""):
    with open(NEWPAGE, 'r') as file:
        newpage_content = file.read()
        
    # newpage_content = re.sub(r'\:root \{ --primary-color\: \#[A-Za-z0-9]{6}', ":root { --primary-color: #"+color, newpage_content)
    
    # Parse the HTML content using BeautifulSoup
    newpagesoup = BeautifulSoup(newpage_content, 'html.parser')

    titletag = newpagesoup.find("a", "article-title")
    if titletag is not None:
        titletag.string.replace_with(title)
        titletag['href'] = url
    
    titletag = newpagesoup.find("title")
    if titletag is not None:
        titletag.string.replace_with(title)

    if author is not None:
        authortag = newpagesoup.find("span", "author")
        if authortag is not None:
            if authortag.find("a") is not None:
                authortag.find("a").string.replace_with(author)
    else:
        print("ERROR! nie ma autora!")
    
    if newpagesoup.find("article", "article-input") is None:
        print("ERROR! nie ma article.article-input w "+NEWPAGE)    
    else:
        if soup.find("article", "article-input") is None:
            print("ERROR! nie ma article.article-input w tym co wstawiam!")
        else:
            newpagesoup.find("article", "article-input").replace_with(soup.find("article", "article-input"))
    
    return newpagesoup  

def correct_html(html_content):
    # pandoc zamiast \qed tworzy 0[], a nie []
    html_content = html_content.replace("0"+u"\u25FB", u"\u25FB")
    html_content = html_content.replace("deltaColor", "var(--primary-color)")
    html_content = html_content.replace("#"+COLOR, "var(--primary-color)")

    html_content = re.sub(r'<div class="answer">\s*\n?\s*<p>\s*<strong>Rozwiązanie(\s+[0-9]+)?</strong>\. ', '<!-- EXERCISE MIDDLE--> <header class="answer"><a href="javascript:void(0)">Rozwiązanie</a></header><div class="answer-content">\n', html_content, flags=re.DOTALL)

    html_content = re.sub(r'<div class="exercise">\s?<p><strong>Zadanie(\s*[0-9]+)?</strong>.\s*<span>(M\s+[0-9]+)\.</span>', r'<div class="exercise"><!-- EXERCISE BEGIN -->\n<header class="exercise">Zadanie \2</header><p>', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<div class="exercise">\s?<p><strong>Zadanie(\s*[0-9]+)?</strong>.\s*<span>(F\s+[0-9]+)\.</span>', r'<div class="exercise"><!-- EXERCISE BEGIN -->\n<header class="exercise">Zadanie \2</header><p>', html_content, flags=re.DOTALL)
    
    if re.findall('<header class="exercise">Zadanie M', html_content):
        autor1 = "XXX"
        autor2 = "XXX"
        for a in re.findall(r'(<span>Przygotował (.*?)</span>)', html_content):
            if autor1 == "XXX":
                autor1 = a[1]
                html_content = html_content.replace(a[0], '')
            else:
                if autor2 == "XXX":
                    autor2 = a[1]
                    html_content = html_content.replace(a[0], '')
        
        html_content = re.sub(r'(<div class="exercise"><header class="exercise">Zadanie M)', r'<p><span><em>Przygotował '+autor1+r'</em></span></p>\1', html_content, 1, flags=re.DOTALL)
        html_content = re.sub(r'(<div class="exercise"><header class="exercise">Zadanie F)', r'<hr /><p><span><em>Przygotował '+autor2+r'</em></span></p>\1', html_content, 1, flags=re.DOTALL)
        
    soup = BeautifulSoup(html_content, 'html.parser')
    title = ""
    author = ""
    url = "#"
    if soup.find("h1", "title"):
        title_tag = soup.find("h1", "title")
        for span_tag in title_tag.find_all("span"):
            if span_tag.string is not None and span_tag.string.strip() == "":
                span_tag.extract()
        title = title_tag.get_text()

    if soup.find("p", "author"):
        author = soup.find("p", "author").string
        
    for header_tag in soup.find_all("header", {"id": "title-block-header"}):
        header_tag.extract()

    for footnotes in soup.find_all("section", {"id": "footnotes"}):
        for li_tag in footnotes.find_all("li"):
            if li_tag.has_attr('id'):
                match = re.match(r'^fn([0-9]+)$', li_tag['id'])
                if match:
                    for blockquote in li_tag.find_all("blockquote"):
                        blockquote['id'] = "blockquote-"+match.group(1)
                        del blockquote['class']
                        blockquote['class'] = "blockquote-margin"
                if li_tag.find("a", "footnote-back") is not None:
                    li_tag.find("a", "footnote-back").extract()
                li_tag.replaceWithChildren()        

        footnotes.name = "div"
        del footnotes['class']
        footnotes['class'] = "article-input-margin"
        for hr in footnotes.findChildren("hr", recursive=False):
            hr.replaceWithChildren()
                
        if footnotes.find("ol") is not None:
            footnotes.find("ol").replaceWithChildren()
    
    for footnote_ref in soup.find_all("a", "footnote-ref"):
        block_id = "blockquote-"
        if footnote_ref.has_attr('id'):
            match = re.match(r'^fnref([0-9]+)$', footnote_ref['id'])
            if match:
                block_id = block_id + match.group(1)
                
        span = BeautifulSoup("<span id='span-"+block_id+"' class='span-blockquote-ref'></span>", "html.parser")
        footnote_ref.replace_with(span)    
    
    for footnotes in soup.find_all("div", "article-input-margin"):
        for blockquote in footnotes.find_all("blockquote"):
            if blockquote.has_attr('id'):
                span = soup.find("span", {"id": "span-"+blockquote['id']})
                if span is not None:
                    p = span.find_parent("p")
                    if p is not None:
                        if span.previous_sibling is None:
                            p.insert_before(blockquote)
                        else:
                            while(p.next_sibling is not None and p.next_sibling.name == "blockquote"): 
                                p = p.next_sibling
                            p.insert_after(blockquote)
                    else:
                        span.insert_after(blockquote)

    for span_tag in soup.find_all("span"):
        if span_tag.string == ",":
            span_tag.replace_with(",")

    for span_tag in soup.find_all("span"):
        if span_tag.has_attr('style') and span_tag['style'] == "color: blue":
            del span_tag['style']
            span_tag.name = "strong"
        if span_tag.has_attr('style') and span_tag['style'] == "color: blue" and span_tag.find("strong"):
            span_tag.replaceWithChildren()

    article = soup.find("body")
    if article is None:
        print("- !!! Nie ma body!")
        return

    article.name = "article"
    article['class'] = ['article-input'] + ['article-from-tex']

    article_div = soup.new_tag("div")
    article_div['class'] = "article-input-div"
    if article.find("div", "article-input-margin"):
        article_div.append(article.find("div", "article-input-margin"))
    else:
        print("- !!! Uwaga! Nie ma div.article-input-margin")

    soup = add_links_to_delta(soup)
            
    main_text = soup.new_tag("div")
    main_text['class'] = "article-input-main-text"
    for el in article.findChildren(recursive=False):
        main_text.append(el.extract())
        main_text.append("\n\n")
    article_div.insert(0,main_text)

    article.append(article_div)
        
    newsoup = replace_article_in_newpage(soup, title, author, url)
    
    return newsoup

if __name__ == '__main__':
    convert_to_html()
    
