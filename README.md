#### INSTRUKCJA OBSŁUGI #########

## POCZĄTEK ##

STEP 0: ŹRÓDŁA 
0.1 Skopiować do katalogu 2025-01 źródła Delty (zawartość katalogu z plikami TeX, np. 2025-01-delta.tex; ostatnio nazywał się druk)
0.2 Przenazwać plik z zadaniami (np. 2412-zadania-rozw.tex) na 20-zadania.tex, dodać do jego początku fragment w którym są wywoływane (czyli końcówkę któregoś z początkowych plików TeX z komendami \zadMat itp) - tego już nie trzeba - to robi b1_prepare_zadania.py

STEP 1: STWORZENIE OSOBNYCH PLIKÓW TEX 
1.1 Wpisać do config.py wersję wydania (np. 2025-01)
1.1 Odpalić python convert-1-move-from-issue.py

## GŁÓWNA ROBOTA ##

STEP 2: PLIKI TEX -> HTML
2.0 (opcjonalnie) Odpalić ./convert-2-html.sh 2025-01 (uruchamia poniższą komendę dla wszystkich plików)

2.1 Odpalić python convert-py-2-html.py 2025-01-figures delta-2025-01-art-XX-cos.tex
2.2 Obejrzeć delta-2025-01-art-XX-cos.html
2.3 Jeżeli HTML nie powstał lub ma błędy - zmieniać delta-2025-01-art-XX-cos.tex i wrócić do 2.1

STEP 3: POPRAWKI W HTMLACH
3.1 Odpalić ./convert-3-clean.sh 2025-01
% Skrypt kasuje pliki pośrednie oraz wszystkie nieużywane pliki z katalogu z obrazkami

3.2 Poprawić HTMLe, w szczególności przerobić tekst na zadania z rozwijanymi odpowiedziami.
Przy Bzdędze wkleić:

<!-- EXERCISE BEGIN -->
<div class="exercise">
  *** tu treść zadania ***
  <!-- EXERCISE MIDDLE-->
  <header class="answer">
    <a href="javascript:void(0)">Wskazówka</a>
  </header>
  <div class="answer-content"> 
  *** tu wskazówka ***
  <!-- EXERCISE END   -->
  </div>
</div>

Dla Ligi (jeżeli jest omówienie zadań) powinno być:

<!-- EXERCISE BEGIN --> <div class="exercise">
*** tu treść zadania ***
<!-- EXERCISE MIDDLE--> <header class="answer"><a href="javascript:void(0)" style="color: var(--primary-color)">Rozwiązanie</a></header><div class="answer-content" style='color:#000000'>
*** tu rozwiązanie ***
<!-- EXERCISE END   --> </div></div>

## ZAKOŃCZENIE GŁÓWNEJ ROBOTY ##

STEP 4: HTML -> DELTAMI
4.1 Odpalić skrypt ./convert-4-cut-out-article.sh 2025-01

4.2 Przekopiować zawartość HTMLi z delta-2025-01-xxxx-article.html do deltami.edu.pl/admin (sortuj po issue)
4.3 Przekopiować katalog 2025-01-figures na serwer Delty do katalogu /home/delta/delta-dev.mimuw.edu.pl/delta/media/ . Upewnić się, że pliki mają dobre uprawnienia (644).

STEP 5: KONIEC
5.1 Odpalić skrypt ./convert-5-archive.sh 2025-01


#### INFO ####

Ogólne informacje:

1. Skrypty napisane są w bashu i pythonie.
Wykorzystują: pdflatex, pandoc, imagemagick.
Ja tworzyłem je i używałem na MacOS.

2. Jest tu trochę skryptów, które wykonują operacje na wszystkich plikach:

> convert-1-move-from-issue.sh 

Skrypt (w oparciu o źródła z katalogu 2025-01) tworzy osobne pliki TeX artykułów, przenosi wszystkie obrazki do katalogu 2025-01-figures, konwertuje do PNG, poprawia ścieżki do obrazków, usuwa komentarze, ... 
W wyniku jego działania powinien dla każdego artykułu powstać plik delta-2025-01-art-XX-something.tex

Wykorzystuje skrypty convert-py-0-pdf2png.sh i convert-py-1-move-from-issue.py

> convert-2-html.sh

W idealnym świecie konwertuje pliki TeX artykułów na HTML. O nim niżej. 
W wyniku jego działania powinien dla każdego artykułu powstać plik delta-2025-01-art-XX-something.html

Wykorzystuje skrypt convert-py-2-html.py

> convert-3-clean.sh

Prosty skrypt kasujący pliki pośrednie oraz wszystkie nieużywane pliki z katalogu z obrazkami.
Wykorzystuje convert-py-3-clean.py

> convert-4-cut-out-article.sh

Prosty skrypt wycinający z każdej strony delta-2025-01-art-XX-something.html samą treść artykułu i poprawia w nim ścieżki do obrazków.
W wyniku jego działania dla każdego artykułu powstaje plik delta-2025-01-art-XX-something-article.html

> convert-5-archive.sh

Prosty skrypt przenosi pliki .tex, .html i -article.html oraz katalog z wykorzystywanymi obrazkami do podkatalogu 2025-01-gotowe.

3. Sama konwersja TEX -> HTML (convert-py-2-html.py) działa dla pojedynczego dowolnego pliku LaTeXowego artykułu Deltowego i ma parę kroków:
- najpierw tworzy plik TeX (....-tikz.tex) i odpala na nim pdflatex aby stworzył obrazki, które generuje TikZ
- następnie przygotowuje uproszczony plik (...-pandoc.tex) i odpala na nim pandoc, który konwertuje tex na html
- następnie przerabia utworzoną stronę (...-pandoc.html) na właściwy html (....html)

4. Przy konwersji najwięcej roboty jest z obrazkami. Dużo obrazków jest generowanych przez TikZa, ale aby je wygenerować pliki LaTeXowe muszą się kompilować, co często nie działa... Może trzeba przestać próbować to robić, a po prostu poprosić aby stworzone pliki były w źródłach. Jeżeli dobrze widzę to w źródłach 12 Krzysiek Rudnik wrzucił chyba takie pliki - jakby one były to znacząco uprościłoby skrypt.

Jeżeli plik się nie kompiluje to jest pisany o tym komunikat i obrazki się nie tworzą (ale strona HTML tak). Jeżeli nie uda mi się tego łatwo poprawić to odpuszczam, wycinam obrazek z gotowego PDFa numeru i nazywam go odpowiednio, np. delta-2025-01-art-02-skibski-skowron-tikz-figure1.png.

Poza tym często w plikach LaTeXowych na obrazki nakładane są literki (np. jest jakiś wykres, a komendami LaTeXowymi dodawane są podpisy linii). Tego pandoc nie wspiera, w takich sytuacjach też trzeba wyciąć obrazek z gotowego PDFa.

5. Zdarza się, że pandocowi nie uda się utworzyć strony HTML, bo czegoś nie zrozumiał, albo coś mu się nie parsuje (np. nawiasy). Pandoc jest dość ubogi i dużo rzeczy z LaTeXa nie rozumie. Dlatego też moje skrypty starają się go upraszczać i na przykład kasować wszystkie ustawienia interlinii itp., które pandoc po prostu by wypisał. LaTeX jest jednak tak bogaty, że czasem i tak coś przeniknie.

Poza tym jeżeli czegoś pandoc nie zrozumie to to kasuje... Można go uruchomić z ostrzeżeniami, ale jest ich tyle, że ciężko coś zobaczyć. Ja zwykle patrzyłem na HTML i na finalny PDF i przeglądałem czy nic z grubsza się nie skasowało (jak się coś kasuje to zwykle dużo, np. cały paragraf). 

6. Poprawki w HTMLach to (na szczęście) głównie poprawianie szerokości obrazków. Starałem się je jakoś ustawiać automatycznie, ale chyba niezbyt to działa. Poza tym jedną rzeczą niezwiązaną stricte z konwersją jest to, że na stronie zamiast wyświetlać rozwiązania/wskazówki to chowamy je i rozwija się je guzikiem. Dla zadań zrobiłem automatyczną konwersję, która tworzy odpowiedni obiekt HTML. Dla innych zadań tego nie ma, dlatego opisałem powyżej jakieś fragmenty HTML, które trzeba powklejać w tym celu do HTMLa. 

7. Warto marginesy poprzestawiać/podzielić i w LaTeXu powkładać tam gdzie są wywoływane.

8. W Delcie jest sporo stałych działów, które działają trochę inaczej niż zwykłe artykuły:

- aktualności/takie jest życie/prosto z nieba/niebo w... - tak naprawdę z nimi nie ma prawie roboty, bo to zwykle czysty tekst. Jedyne co, to autorzy i ich afiliacja są zwykle na dole strony. Mój skrypt stara się ich wyłowić, ale różnie to działa - jak nie zadziała to trzeba na początku artykułu dodać \waut{...} i \aafil{...} i reszta zrobi się automatycznie.

- bzdega - zwykle afiliację trzeba ręcznie przepisać, a wskazówki z marginesu przenieść do zadań i potem już w wygenerowanym HTMLu pozmieniać aby się rozwijały. Pewnie można to łatwo zautomatyzować - tego nie zrobiłem.

- ligi - niesamowicie skomplikowany plik... często są problemy ze skompilowaniem i też czasem z przerobieniem na pandoc... Kasowanie wszystkie poza tym co się wyświetla zwykle pomaga. Jeżeli jest omówienie zadań to trzeba powklejać to rozwijanie do HTMLa. Często marginesy są w złych miejscach.

- zadania - one są zasadniczo w pliku 2501-zadania-rozw.tex . Poza tym dotychczas było tylko ich wywołanie zadań (komendy \zadMat itp.) na końcu któregoś z początkowych artykułów (ten fragment kopiowałem na początek pliku 2501-zadania-rozw.tex, czasem były tu np. obrazki) i rozwiązania w losowych miejscach na marginesie (to można było pominąć). Od paru numerów rozwiązania są na osobnej stronie i mają swój plik. W numerze 12 można go było olać, ale trzeba uważać czy coś nie pojawia się tylko tam.

9. Jak ktoś bardzo udziwnia ten kod LaTeXowy, to różne dziwne rzeczy mogą się dziać. Np. obrazki LaTeXowe są czasem w osobnych plikach (np. u Miśkiewicza), trzeba je wtedy powklejać do głównego. Często ludzie mają jakieś dziwne komendy, a potem pandoc ich nie rozumie. Zasadniczo upraszczając i upraszczając w końcu powinien sobie poradzić :).

