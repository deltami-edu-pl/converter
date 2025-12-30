2025/12/29
+ zrobić FILE() i PATH()
+ zrobić config na nowo trochę

- uprościć config (bez klas?)
- usunąć const - config - color, newpage itd. - albo przerobić
- eksportować tylko obrazki - między \body{document}
- sprawdzać czy korzysta się z \dv i dodawać tylko to przed \body{document}
- czy ktoś edytuje delta.sty? czy to zawsze to samo? czy go kopiować? czy on się inkluduje jakoś


2025/12/28
- ogarnąć ide żeby lepiej podpowiadało + jakiś autodoc + przechodzenie przy klikaniu
- refaktor aa4b_rename_images - uprościć
- przejść krok po kroku z Olą przez aa4c_clean_tex i ac2d_convert_to_html_prepare

2025/12/26
- najpierw generuję wszystkie obrazki - i te z /rys /eps itd i te z latex
- potem robie tylko pandoc

- refaktor convert
    - w jednym kroku usuwam wszystko co niepotrzebne

  - najpierw export i konkwersja obrazków (w jednym kroku)
    - zapisuje "-images" i po koleii generuję obrazki
    - jakiś sensowy log z błędami
  - potem przygotowanie pandoc w drugim kroku
    - zapisuje osobny plik tex
    - w drugim dodaję różne bajery (bibliografię itd.)
  









TODO
- opracować ac1_convert_images
  - wyeksportowanie obrazków do pdf
  - konwersja pdf na png (może w locie?)
  - i chyba tyle



## convert-1-move-from-issue.py
+ przepisać na pythona
+ kopiować tylko obrazki (jpg, png, pdf), pomijać eps itd
+ konwertować w locie pdf na png i zapisywać w figures (nie przenosić)
  + przepisać skrypt convert-py-0-pdf2png.sh na python
+ rozbić skrytp na prepare images
+ autoformatowanie źródeł (tex)
+ zmieniać automatycznie nazwę pliku z zadaniami

+ osobno zrobić to tak
  + globalnie wykonujemy to co trzeba globalnie
  + osobny skrypt bierze pierwszy możliwy artykuł i go przerabia
  + "DONE" przenosi do 2025-05-done

- rozbić c_convert na mniejsze funkcje, zrefaktorować i zrozumieć co tam się dzieje

- 

- static - folder na article.css itd.
- wywalić cząstkowe a_, b_ itd.
- może od początku do końca robić wszystko po jednym pliku?

- usuwać \thickmuskip2mu z texa

idea - mamy plik main.py
  - odpalamy najpierw globalne zadania (przygotowanie tex, obrazki, formatowanie etc) a1, a2, a3, a4
  - potem odpala się tworzenie artykułu (pierwszego) b1, b2, b3
  - potem odpala się serwer c1, c2, c3
  - gdy oznaczymy artykuł jako skończony to przenosi się do finished - opracowuje się nowy artykuł
  - gdy nie ma już artykułów to przenoszą się obrazki na produkcje

potem refaktor
  - obrazki z odpowiednimi ścieżkami od razu
  - być może niepotrzebne pośrednie pliki (html etc)
  - być może formatowanie HTML od razu
  - przejrzeć na końcu skrypty od gościa i porównać
  - usunąć wszystkie inne foldery z konwerterem
  - zrobić dekoratory z print() print('### move_to_done')

- nie przenosić i rozwiązań i tego drugiego

- dokończyć robienie numeru 2025-05

- wywoływać normalnie skrypt convert-py-1-move-from-issue przez import

- może zapisywać do osobnych katalogów obrazki? per artykuł?

równania do których jest odniesienie musza mieć \tag{1} algo \tag{$\star$}, a potem \eqref (zmieniany na $\eqref$ - \ref nie działa)

trimowanie - lepsza jakość, rozmiar obrazków: delta-2021-01-art-03-kostrzewski.html
eps - kolor numeru
\ref i \cite: delta-2023-11-art-05-rotkiewicz
