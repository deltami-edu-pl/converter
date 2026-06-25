# Reguły projektowe

## Stylowanie

- **Nie modyfikuj `static/article.css`** automatycznie. Plik jest synchronizowany ze stylem produkcyjnym Delty i lokalne zmiany w nim ryzykują rozjazd z resztą serwisu. Jeśli problem da się rozwiązać po stronie pipeline-u (skrypty `a3*`, `correct_html`) albo lokalnie w treści artykułu (`.tex` → klasy/style inline w wygenerowanym HTML), to wybieraj te ścieżki.
- Jeśli mimo wszystko widzisz, że jedyne rozsądne wyjście to zmiana w `static/article.css` — **najpierw powiedz to userowi i poczekaj na zgodę**, zamiast wprowadzać zmianę po cichu.

## Pliki źródłowe artykułów

- **`got/<NN>-<slug>.tex`** to nietknięty drop od redakcji — nie edytuj go.
- **`<NN>-<slug>.tex`** w katalogu głównym to **roboczy plik artykułu**, który czyta cały pipeline (`FILE().source.tex`). Wszystkie ręczne poprawki w treści artykułu wprowadzaj **tutaj**.
- **`<NN>-<slug>-article.tex`** to wynik etapu `prepare_pandoc` (po `a3a*`). Plik regenerowany — edycje tu są nadpisywane przy następnym `cp`.
- **`<NN>-<slug>-article.html`** to finalny HTML. Też regenerowany.
- **`<NN>-<slug>-images.tex`** to standalone TeX z ekstrahowanymi tikzpicture, kompilowany do PDF-ów. Regenerowany przez `convert:images`.

## Komendy pipeline-u

Wszystko przez `./main.py <command>` (aliases w nawiasach):

- `prep` (`p`) — przygotowanie z `got/2026-NN-delta.tex` → kopiowanie do roboczych `.tex`.
- `convert:images` (`ci`) — wyciąga `\begin{tikzpicture}` z artykułów do `<artykul>-images.tex`, kompiluje `pdflatex` → konwertuje PDF-y do PNG-ów w `2026-NN-figures/`.
- `convert:pandoc` (`cp`) — pełny pipeline tekstowy: `prepare_pandoc` (`a3a*`) → `pandoc` → `correct_html` (`a3b`) → `convert_zadania` (`a3c`) → `extract_article` (`a3d`). Wynik: `<artykul>-article.html`.
- `convert` (`c`) — `ci` + `cp` razem.
- `done` (`d`) — przenosi gotowe pliki do `2026-NN-done/`.
- `rsync` (`r`) — synchronizuje folder figur (`2026-NN-figures/`) na serwer Delty.
- `push` / `pull` (+ `:css` / `:js`) — wgrywa/ściąga `static/article.css` i `static/article.js` z/na serwer.
- `serve` (`s`) — lokalny dev server.
- `finish` (`f`) — archiwizuje cały numer do `../!DONE/`.

Po edycji **pipeline-u** odpalaj `./main.py cp` (sam pandoc — szybko) lub `./main.py c` (jeśli trzeba zregenerować obrazki). Po edycji **źródła artykułu** — to samo.

## Gdzie poprawiać co

Gdy coś nie działa, najpierw rozumiem **gdzie w pipeline pęka**, a potem edytuję:

- **`pdflatex` wybucha na tikzpicture** (`# ERROR: pdflatex zwrócił błąd`) — brakuje makra w preambule `<artykul>-images.tex`. Patrz `_extract_newcommands_as_provide` w [a2_convert_images.py](a2_convert_images.py). Obsługuje już `\newcommand`, `\def\name{body}`, `\definecolor`, `\colorlet`.
- **`pandoc` wybucha** (`! Pandoc: error: pandoc zwrócił błąd`) — TeX-owa konstrukcja w `<artykul>-article.tex`, której pandoc nie ogarnia. Edytuj [a3a0_clean_tex.py](a3a0_clean_tex.py) (strip TeX-owych prymitywów: `\let`, `\hbox to<dim>`, rejestry długości, `\def\X#1<delim>{...}` z delimiterami w argach) albo [a3a1_prepare_tex.py](a3a1_prepare_tex.py) (`\marg` → `\myquote`, autor, math macros `\R`/`\tg`/`\ctg`, kolapsowanie zagnieżdżonych `\myquote`).
- **HTML wyświetla niepotrzebny tekst typu `to18cm`, `minus20pt`** — TeX-owy rejestr/box wyciekł przez pipeline. Dorzuć regex w [a3a0_clean_tex.py](a3a0_clean_tex.py).
- **HTML ma `\R`/`\tg` jako czerwony tekst zamiast renderu** — brakuje `\newcommand` dla MathJax. Patrz `math_macros` w [a3a1_prepare_tex.py](a3a1_prepare_tex.py).
- **Brakuje obrazka w body HTML, choć PNG się wygenerował** — pewnie pandoc zgubił `\includegraphics` przez jakiś wrapper (`\hbox{\macro}` itp.) lub nestowane `\myquote`. Sprawdź `<artykul>-article.tex` i dorzuć fix w `a3a0`/`a3a1`.
- **Bibliografia / Zadania / Wskazówki / footnotes źle ułożone** — to robi [a3b_correct_html.py](a3b_correct_html.py) (footnotes → margines, wrappy bibliografii) i [a3c_convert_zadania.py](a3c_convert_zadania.py) (parowanie wskazówek z zadaniami).
- **Pojedynczy artykuł ma specyficzny problem niewart generalizacji** — edytuj `<artykul>.tex` w katalogu głównym (NIE `got/`). Np. zmiana rozmiaru czcionki w tikzpicture, owinięcie problematycznego bloku w `\begin{tikzpicture}\node{...};\end{tikzpicture}` żeby pójść ścieżką PDF→PNG zamiast walczyć z pandokiem.

## Drobne gotchy

- `convert:images` używa **TikZ external** — PDF-y trzymane są pod `<artykul>-images-figureN.pdf` w katalogu głównym. Kolejność `figureN` zależy od kolejności tikzpicture w źródle.
- Pliki `_extract_newcommands_as_provide` w `a2` zamienia `\newcommand` na `\providecommand`, żeby uniknąć kolizji z `delta.sty`. Definicje wyciągane są **z body** artykułu (autorzy często definiują makra w środku).
- W body artykułu występują `\def\X#1<delim>...{...}` (np. `\xitem`, `\zz`, `\bbleft`) — pandoc tego nie ogarnia. `a3a0` auto-wykrywa takie defy i albo strippuje wywołania, albo (dla `#1\right` patternów) rozwija `\X<content>\right` → `body[#1:=content]`.
- `\rightline{...}` mapowane jest na `\myquote{...}` w `a3a1`. Gdy zagnieżdżone z `\marg{...}` daje `\myquote{\myquote{...}}` — collapse w `_collapse_nested_myquote`.
- `delta.sty` jest dołączane tylko do `pdflatex` w `convert:images`. Pandoc ignoruje `\usepackage{delta}`, więc makra z `delta.sty` (np. `\R`) muszą być **dodatkowo** wstrzyknięte do `<artykul>-article.tex` przez `a3a1`.
