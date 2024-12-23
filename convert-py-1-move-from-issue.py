import re
import sys
import os

used_names = []

# usuwa zawartosc komentarzy oraz linie, w ktorych sa tylko komentarze
def remove_comments(content):
    content = re.sub(r'(?<=[^\\])%.*', '%', content)
    content = re.sub(r'\n([ \t]*%\n)*','\n', content) 
    content = re.sub(r'(?<=\~)\%\n','', content, re.DOTALL)
    
    return content

def crop_image(figures_folder, name, params):
    name_noext = re.sub(r'\.[a-zA-Z0-9_]+$', '', name)
    new = name

    if not os.path.exists(figures_folder+"/"+name):
        print("!! Figure "+name+" does not exist.")

    trim_match = re.match(r'^\[trim=\{?([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)\}?,',params)
    if not trim_match:
        return ""
    print("- I am trimming figure "+name)

    j=1
    while name_noext+"-crop-"+str(j)+".png" in used_names: 
        j=j+1
    new_pdf = name_noext+"-crop-"+str(j)+".pdf"
    new = name_noext+"-crop-"+str(j)+".png"

    os.system("convert -crop +"+trim_match[1]+"0+"+trim_match[4]+"0 -crop -"+trim_match[3]+"0-"+trim_match[2]+"0 -density 720x720 +repage "+figures_folder+"/"+name+" "+figures_folder+"/"+new_pdf)
    os.system("convert -density 600 -transparent white -colorspace sRGB -limit memory 64MB -limit map 128MB "+figures_folder+"/"+new_pdf+" "+figures_folder+"/"+new)
    
    used_names.append(new)
    return new

if len(sys.argv) < 4:
    print("Usage: python xxxxx.py <main_file> <filename> <filename_new> <figures_folder>")
    exit(1)

main_file = sys.argv[1]
filename = sys.argv[2]
filename_new = sys.argv[3]
figures_folder = sys.argv[4]
filename_noext = re.sub(r'\.[a-z]+$', '', filename)

try:
    # START OF MERGING
    with open(main_file, 'r') as file:
        content_main = file.read()
    
    start_position = content_main.find("\\begin{document}")
    if start_position != -1:
        content_main = content_main[:start_position]
    
    with open(filename, 'r') as file:
        content = file.read()

    end_position = content.find("\\endinput")
    if end_position != -1:
        content = content[:end_position]
    
    content = content_main + "\\begin{document}\n" + content + "\\end{document}"

    content = remove_comments(content)
    content = re.sub(r'\\includeonly\{[^\}]*\}', '', content)
    content = re.sub(r'\\input\{[^\}]*\}', '', content)
    content = re.sub(r'\\input\ ?[^\\\ ]*', '', content)
    
    # END OF MERGING
    
    # zamiana sciezek - wszystkie obrazki sa w figures/ oraz pdfy zostaly przerobione na png i sa includowane teraz
    matches = re.findall(r'(\\includegraphics(\[[^\]]*\])?\%?\s*?\{([^\}]*)\})', content, re.DOTALL)
    matches2 = re.findall(r'(\\img(\[[^\]]*\])?\{([^\}]*)\})', content, re.DOTALL)
    matches = matches + matches2
    extensions = ["png", "jpg", "jpeg", "PNG", "JPG", "JPEG"]
    
    for match in matches:
        match_all = os.path.basename(match[2])
        match_noext = re.sub(r'\.[a-zA-Z0-9_]+$', '', match_all)
        match_ext = re.search(r'\.([a-zA-Z0-9_]+)$', match_all)
        new = match_all
        params = match[1]

        if match_ext:
            if match_ext.group(1)=="pdf":
                new = match_noext+".png"
                
                maybe_new_name = crop_image(figures_folder, match_all, params)
                if not maybe_new_name == "":
                    new = maybe_new_name
                    params = re.sub(r'^\[trim=\{?([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)\}?,','[', params)
            
            if match_ext.group(1)=="eps":
                new = match_noext+"-eps-converted-to.png"
        else: 
            if os.path.exists(figures_folder+"/"+match_noext+".pdf"):
                new = match_noext+".png"
                maybe_new_name = crop_image(figures_folder, match_noext+".pdf", params)
                if not maybe_new_name == "":
                    new = maybe_new_name
                    params = re.sub(r'^\[trim=\{?([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)\}?,clip,','[', params)
                    params = re.sub(r'^\[trim=\{?([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)\}?(,clip)?,','[', params)
            else:
                i = 0;
                while i < len(extensions) and not os.path.exists(figures_folder+"/"+match_noext+"."+extensions[i]):
                    i = i+1
                if i < len(extensions) :
                    new = match_noext+"."+extensions[i];
                else:
                    if os.path.exists(figures_folder+"/"+match_noext+".eps"):
                        match_noext = match_noext + "-eps-converted-to"
                    i = 0;
                    while i < len(extensions) and not os.path.exists(figures_folder+"/"+match_noext+"."+extensions[i]):
                        i = i+1
                    if i < len(extensions) :
                        new = match_noext+"."+extensions[i];
                
        if not os.path.exists(figures_folder+"/"+new):
            print("Figure "+new+" does not exist.")
    
        content = content.replace(match[0], "\\includegraphics" + params + "{"+figures_folder+"/"+new+"}")
    
    with open(filename_new, 'w') as file:
        file.write(content)
        
except Exception as e:
    print(f"An error occurred: {str(e)}")
