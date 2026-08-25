"""
Reguly zamiany pozycji numeru na rekord artykulu w panelu admina.

Wyprowadzone z RECZNIE wprowadzonego numeru 2026-09 (issue 898) - nie zgadywane.
Klucz to makro tytulu z pliku .toc; zob. articles.toc_entries().
"""

# makro w .toc -> slug kolumny w serwisie ("" = bez kolumny)
COLUMN_BY_MACRO = {
    "poz": "",
    "ko": "kat-otwarty",
    "kpo": "kacik-poczatkujacego-olimpijczyka",
    "tjzwspisie": "takie-jest-zycie",
    "akts": "aktualnosci",
    "liga": "klub-44",
    "pzn": "prosto-z-nieba",
    "niebow": "niebo-w",
    "zadania": "zadania",
}

# makra bezargumentowe maja tytul ustalony przez redakcje
FIXED_TITLE = {
    "liga": "Klub 44",
    "zadania": "Zadania",
}

# makra, w ktorych nazwa kolumny wchodzi do tytulu jako prefiks
TITLE_PREFIX = {
    "akts": "Aktualności",
    "pzn": "Prosto z nieba",
}

# kolumna wykrywana z prefiksu tytulu, gdy makro jest ogolne (\poz)
COLUMN_BY_TITLE_PREFIX = {
    "Informatyczny kącik olimpijski": "informatyczny-kacik-olimpijski",
    "Mała Delta": "mala-delta",
    "Deltoid": "deltoid",
}

PL = str.maketrans({
    "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n",
    "ó": "o", "ś": "s", "ź": "z", "ż": "z",
    "Ą": "a", "Ć": "c", "Ę": "e", "Ł": "l", "Ń": "n",
    "Ó": "o", "Ś": "s", "Ź": "z", "Ż": "z",
})
