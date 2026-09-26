# Wydanie numeru

Dwie fazy z bramką po środku. Faza 1 nie dotyka niczego na zewnątrz. Faza 2
dotyka produkcji i każdy jej krok wymaga `--apply`.

## Faza 1 — przygotowanie

```
./main.py release:prepare
```

Robi po kolei: `dropbox:pull` (jeśli nie ma `got/`) → `prep` → `convert:all` →
`admin:map` → `checks`. Na końcu wypisuje liczbę błędów i adres przeglądu.

```
./main.py review        # http://127.0.0.1:5000/
```

Indeks pokazuje pozycje **w kolejności z druku** (z `got/*-delta.toc`), obok
każdej stronę z PDF-a numeru. Kolumna „checki" to wynik asercji layoutu.

### Bramka

Przejrzyj artykuły. Zielone checki nie zwalniają z obejrzenia — sprawdzają
geometrię, nie sens. Szczególnie:

- marginalia nie sięgają niżej niż treść (check to mierzy, ale zapas bywa
  kilkudziesięciopikselowy)
- obrazki są tam, gdzie w druku, i w rozsądnej skali
- formuły się renderują (czerwony tekst = błąd MathJaxa)

Uzupełnij `division` w `<numer>-output/admin-map.json` — nie wynika z `.toc`.

## Faza 2 — publikacja

```
./main.py release:publish                                  # dry-run
./env/bin/python a15_release.py publish --issue <ID> --apply
```

`<ID>` to `journal_issue.id` z panelu admina, nie numer Delty.

Kolejność: `done_all` → `dropbox:push` → `paper:links` → `admin:upload` →
`rsync`. Każdy krok bez `--apply` tylko raportuje.

### Ręcznie na końcu

1. wklej `<numer>-output/paper-links.md` do Paper doca — **nad** najnowszą
   sekcję, nowy numer idzie na górę
2. włącz `published` na artykułach w panelu
3. `./main.py finish` — archiwizacja do `../!DONE/`

## Poszczególne kroki

| komenda | skrót | co robi |
|---|---|---|
| `dropbox:pull` | `dp` | drop redakcji → `got.zip` + `got/` |
| `prep` | `p` | `got/` → roboczne `.tex` w rootcie |
| `convert:all` | `ca` | wszystkie artykuły → `-article.html` |
| `convert` | `c` | jeden artykuł (pierwszy w rootcie) |
| `checks` | `k` | asercje layoutu w Playwright |
| `admin:map` | `am` | `<numer>-output/admin-map.json` |
| `review` | `v` | przegląd na `127.0.0.1:5000` |
| `dropbox:push` | `dph` | `html.zip` na Dropboxa |
| `paper:links` | `pl` | fragment z adresami |
| `rsync` | `r` | figury na serwer |
| `finish` | `f` | archiwizacja numeru |

## Gdy coś pęka

Objaw → plik. Pełna mapa w `CLAUDE.md`.

## Czego nie robi automat

- **`division`** — uzupełniasz w mapie
- **Paper doc** — generujemy fragment, wklejasz ręcznie (zapis wymagałby
  przesłania całej treści, a starsze sekcje mają obrazki)
- **`published`** — włączasz w panelu
- **podział artykułu na dwa** — jeśli spis treści ma osobną pozycję dla
  sekcji wewnątrz pliku (2026-09: „O obozie Math Beyond Limits"), wytnij ją
  do osobnego `.tex` przed `convert:all`
