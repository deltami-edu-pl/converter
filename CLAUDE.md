# Reguły projektowe

## Stylowanie

- **Nie modyfikuj `static/article.css`** automatycznie. Plik jest synchronizowany ze stylem produkcyjnym Delty i lokalne zmiany w nim ryzykują rozjazd z resztą serwisu. Jeśli problem da się rozwiązać po stronie pipeline-u (skrypty `a3*`, `correct_html`) albo lokalnie w treści artykułu (`.tex` → klasy/style inline w wygenerowanym HTML), to wybieraj te ścieżki.
- Jeśli mimo wszystko widzisz, że jedyne rozsądne wyjście to zmiana w `static/article.css` — **najpierw powiedz to userowi i poczekaj na zgodę**, zamiast wprowadzać zmianę po cichu.
