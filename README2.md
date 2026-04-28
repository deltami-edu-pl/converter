step by step
- source env/bin/activate
- python server.py

- niestety najpierw to wszystko przepisuje byc może z lekkimi modyfikacjami
- potem robie większe modyfikacje
- i lecę totalnie od góry 



- pozbyć się tych idotycznych prefików
- pozbyć się przekazywania parametrów parametrów
- dodać formatowanie tex i html
- pozbyć sie skryptów sh




- chciałbym móc pojedynczy plik przerobić z tex na html i tyle!

od końca
- article.html powstaje z
- delta-2025-02-*.html (ale nie pandoc i nie -article) a on powstaje z
- delta-2025-02 -pandoc.html


potrzebuję
- jeden docelowy plik html article z odpowiednimi obrazkami
- jeden *.tex z podmienionymi obrazkami (pandoc)
- jeden *.tex z poprawionym formatowanie etc.


ls *.py | entr -r sh -c 'pkill -f "python server.py"; python server.py'

sudo tlmgr install tkz-euclide tkz-base pgf


- Download "druk.zip" from dropbox with latex files
- Rename "druk" to "2025-01"
- Rename "2501-zadania-rozw.tex" to "14-zadania.tex"
- Copy "\zadMat" section to "14-zadania.tex"
- Copy delta-converter sources files
- Create virtual env python3 -m venv env
- Run virtual env source env/bin/activate
- Install reqs pip install -r requirements.txt




naprawa kolorów
- dodanie klamer { } w tekście
- ale pandoc działa


Instalacja pakietów
- albo `sudo tlmgr install upgreek`
- albo
cd /usr/local/texlive/2024basic/texmf-dist/tex/latex
open .
pobranie z https://ctan.org/pkg/upgreek
przerzucenie
odpalenie `sudo mktexlsr`
sprawdzenie `sudo kpsewhich upgreek.sty`




refaktor
- pozmieniać skrypty bash na python
- zrobić wszystko w jednym ruchu na raz
- środowisko testowe
- ogarnąć jakoś obrazki (być może w ogóle pozbyć się kroku z obrazkami)
