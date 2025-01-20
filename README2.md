- Download "druk.zip" from dropbox with latex files
- Rename "druk" to "2025-01"
- Rename "2501-zadania-rozw.tex" to "14-zadania.tex"
- Copy "\zadMat" section to "14-zadania.tex"
- Copy delta-converter sources files
- Create virtual env python3 -m venv env
- Run virtual env source env/bin/activate
- Install reqs pip install -r requirements.txt
- 



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


python convert-py-2-html.py 2025-01-figures delta-2025-01-art-01-skibski.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-02-miskiewicz.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-03-szymanek.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-04-hansdorfer.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-05-tjz.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-06-aktualnosci.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-07-lukaszewicz.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-08-lehman.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-09-ligi.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-10-pzn.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-11-niebo.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-12-rozwiazania.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-13-bzdega.tex
python convert-py-2-html.py 2025-01-figures delta-2025-01-art-14-zadania.tex


scp -r 2025-01-figures delta:/home/delta/delta-dev.mimuw.edu.pl/delta/media

./convert-3-clean.sh 2025-01
./convert-4-cut-out-article.sh 2025-01


refaktor
- pozmieniać skrypty bash na python
- zrobić wszystko w jednym ruchu na raz
- środowisko testowe
- ogarnąć jakoś obrazki (być może w ogóle pozbyć się kroku z obrazkami)
