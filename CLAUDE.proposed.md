# Konwerter Delty

Zamienia TeX-owy drop redakcji na HTML artykułów dla deltami.edu.pl.

- **Jak pracujemy** (styl, granice zmian) → `AGENTS.md`
- **Jak wydać numer** (kolejność kroków) → `RUNBOOK.md`
- **Ten plik** → fakty o tym repo, których z kodu nie widać

## Zakazy są testami, nie zdaniami

Nie ma tu listy „nie wolno". Każdy zakaz, który dało się wyrazić wykonywalnie,
siedzi w `tests/test_guards.py` — bo regule w pliku instrukcji można zaprzeczyć
jednym zdaniem, a testowi nie.

```
./main.py test
```

| co pilnuje | test |
|---|---|
| `static/article.css` niezmieniony | `ArticleCssIsFrozen` (suma kontrolna) |
| nic nie usuwa zdalnych danych | `NothingDeletesRemoteData` |
| brak POST-a na `/change/` w panelu | `NothingDeletesRemoteData` |
| zapis do Dropboxa wymaga `enable_writes()` | `DropboxWritesAreGated` |
| zapis tylko w jednym folderze, nigdy w `got.zip` | `WriteAllowlist` |
| `\iffalse` wycinane, `\else` respektowany | `DisabledTexBlocks` |
| slug zgodny z adresami na stronie | `SlugConvention` |
| upload domyślnie nie pisze | `AdminUploadDefaultsToDryRun` |

Jeśli któryś test przeszkadza, to znak, że zmiana wymaga rozmowy — nie że test
należy poprawić. Wyjątek: `article.css.sha256` aktualizujesz świadomie, po
uzgodnieniu zmiany w stylu produkcyjnym.

Zostają dwie reguły, których nie umiem sprawdzić kodem:

- **`got/` to nietknięty drop.** Poprawki treści idą do `<NN>-<slug>.tex`
  w rootcie. (`prep` modyfikuje `got/` legalnie, więc suma kontrolna nie
  zadziała.)
- **Pojedynczy artykuł z dziwnym problemem — nie generalizuj.** Popraw jego
  `.tex` w rootcie, np. owijając problematyczny blok w
  `\begin{tikzpicture}\node{...};\end{tikzpicture}`, żeby poszedł ścieżką
  PDF→PNG zamiast walczyć z pandokiem.

## Pliki artykułu

| plik | rola |
|---|---|
| `got/<NN>-<slug>.tex` | drop redakcji |
| `<NN>-<slug>.tex` | **roboczy** — tu wprowadzasz poprawki treści |
| `<NN>-<slug>-article.tex` | wynik `a3a*`, regenerowany |
| `<NN>-<slug>-article.html` | finalny HTML, regenerowany |
| `<NN>-<slug>-images.tex` | standalone TeX z tikz → PDF → PNG |
| `<numer>-output/` | gotowe artykuły, mapa, checki, cache stron PDF |

Regenerowany znaczy regenerowany: ręczna poprawka w `-article.*` przepadnie przy
następnym przebiegu. Jeśli jest systemowa — przenieś ją do pipeline'u.

## Kolejność numeru bierz z `.toc`

`got/*-delta.toc` jest jedynym wiarygodnym źródłem kolejności i tytułów.
Komentarze `%\include{...}` są **nieaktualne** — redakcja składa finalny PDF ze
wszystkim i dopiero potem wyłącza pozycje na próbne kompilacje (2026-09:
`04-tjz` i `08-rajkowski` oznaczone jako wyłączone, oba w druku).

Wpis `\zadania` wskazuje na scalony `NN-rozwiazania`: treść zadań jest w druku
wcześniej niż rozwiązania, ale `a1b_merge_zadania` scala je w plik o najwyższym
numerze. Bez tego mapowania zadania lądują na końcu numeru — tak było we
wszystkich dotychczasowych wpisach.

## Objaw → plik

| objaw | gdzie szukać |
|---|---|
| `pdflatex` wybucha na tikzpicture | `_extract_newcommands_as_provide` w `a2` — brak makra w preambule standalone'u (ogarnia `\newcommand`, `\def`, `\definecolor`, `\colorlet`, `\tikzset`, `\tikzstyle`) |
| `pandoc` wybucha | `a3a0_clean_tex.py` (prymitywy TeX-a, `\def` z delimiterami) albo `a3a1_prepare_tex.py` |
| śmieci w HTML (`to18cm`, `minus20pt`) | `a3a0` — wyciekł rejestr długości |
| `\R`/`\tg` czerwone | `math_macros` w `a3a1` — `delta.sty` widzi tylko `pdflatex` |
| **cała** formuła czerwona | makro z delimiterem nie rozwinęło się; `a3a0` rozwija iteracyjnie, bo TeX też tak robi |
| brak obrazka, choć PNG jest | pandoc zgubił `\includegraphics` przez wrapper (`\hbox`, `\llap`, `\setbox`) lub zagnieżdżony `\myquote` |
| osierocony PNG w `figures/` | tikz wyrenderowany, nie podlinkowany — sprawdź `\iffalse`, `\scalebox`, hoistowane `\def` |
| bibliografia / zadania / wskazówki | `a3b_correct_html.py`, `a3c_convert_zadania.py` |
| marginalia poniżej treści | `article.js` układa je 500 ms po `ready`; mierzy `a9_checks.py` — w statycznym HTML tego nie widać |

## Fakty o serwisie

- **Brak API** — `/api/` → 404, `INSTALLED_APPS` bez `rest_framework`.
- **Brak zapisywalnego stagingu** — katalog o nazwie `delta-dev` obsługuje
  `deltami.edu.pl`, a `db.sqlite3` to żywa baza.
- Odrzuca **403** żądania bez przeglądarkowego `User-Agent`.
- `Article.order` jest **globalnie narastający**, nie per numer.
- `Article.text` to `CharField(50000)` — dłuższy HTML zostanie odrzucony.
- Autorzy idą przez inline `authorshipinfo_set`, nie przez proste pole.
- Ubuntu 20.04, Python 3.8, Django 3.2, Apache + mod_wsgi jako user `delta`,
  brak repo git. Restart aplikacji: `touch wsgi.py`.

## Gotchy pipeline'u

- `delta.sty` dołączane jest **tylko** do `pdflatex`; jego makra muszą być
  dodatkowo wstrzykiwane do `-article.tex` przez `a3a1`.
- Autorzy definiują makra **w środku** artykułu — dlatego `a2` hoistuje je do
  preambuły. Definicje zawierające całe `tikzpicture` są **pomijane**: inaczej
  obrazek renderuje się dwa razy i numeracja `figureN` rozjeżdża się z `a3a3`.
- Idempotencja uploadu idzie po **slugu**. Tytuły różnią się typografią
  (`słowo…` vs `słowo. . .`) i dopasowanie po nich tworzy duplikaty.
- `convert:all` celuje w artykuł przez `config.set_target` i **nie przekłada
  plików**. Nie wracaj do przenoszenia — to była przyczyna nadpisywania
  ręcznych poprawek.
