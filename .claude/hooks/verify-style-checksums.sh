#!/usr/bin/env bash
# Po kazdej komendzie Basha sprawdza, czy pliki stylu sa nadal te same.
#
# Poprzednia wersja byla hookiem PreToolUse dopasowujacym TEKST komendy. Nie da
# sie tego zrobic dobrze: hook widzi caly string i nie odroznia zawartosci
# heredoca od celu zapisu. W efekcie zablokowal kolejno: zwykly grep z "2>&1",
# commit ktory opisywal te regule, i edycje samego siebie.
#
# Sprawdzanie sumy kontrolnej PO wykonaniu jest precyzyjne - patrzy na plik,
# nie na zdanie o pliku. Nie zapobiega zapisowi, ale zglasza go natychmiast
# i lapie kazda droge: heredoc, Python, cp, cokolwiek.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

changed=""
for name in article.css article.js; do
  file="static/$name"
  recorded="static/$name.sha256"
  [ -f "$file" ] && [ -f "$recorded" ] || continue
  actual=$(shasum -a 256 "$file" 2>/dev/null | cut -d' ' -f1)
  expected=$(tr -d '[:space:]' < "$recorded")
  if [ -n "$actual" ] && [ "$actual" != "$expected" ]; then
    changed="$changed $name"
  fi
done

[ -z "$changed" ] && exit 0

reason="Zmienily sie pliki stylu:$changed. Sa zsynchronizowane z produkcja Delty - cofnij zmiane (git checkout -- static/) i napraw problem w pipelinie (a3*) albo w zrodle artykulu. Jesli zmiana jest uzgodniona z userem, zaktualizuj zapisana sume kontrolna."
jq -n --arg r "$reason" '{decision: "block", reason: $r, systemMessage: $r}'
exit 0
