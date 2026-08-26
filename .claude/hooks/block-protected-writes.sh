#!/usr/bin/env bash
# Blokuje Bashowe ZAPISY do plikow stylu.
#
# Deny na Edit/Write nie wystarcza: settings.local.json ma "Bash" na allow-liscie,
# wiec heredoc albo skrypt Pythona obchodzi kazda regule narzedziowa.
#
# ZAKRES jest swiadomie waski - tylko dwa wzorce, w ktorych plik jest
# jednoznacznie celem zapisu. Szersze heurystyki (cp/mv/tee, zapis z Pythona)
# byly tu wczesniej i blokowaly komendy, ktore jedynie WSPOMINAJA sciezke:
# grep z "2>&1", a potem commit opisujacy te regule. Hook widzi caly string
# komendy i nie odroznia zawartosci heredoca od celu zapisu, wiec dokladniejsza
# heurystyka po prostu nie istnieje.
#
# Druga warstwa jest w tests/test_guards.py: suma kontrolna wylapie kazda
# zmiane, ktora tu przejdzie. Lepiej mala luka pod testem niz blokada
# uniemozliwiajaca prace.
set -uo pipefail

P='static/article\.(css|js)'

command=$(jq -r '.tool_input.command // empty' 2>/dev/null)
[ -z "$command" ] && exit 0

blocked=0
# przekierowanie do pliku:  > plik   >> plik   ("2>&1" nie pasuje - po > jest &1)
printf '%s' "$command" | grep -Eq ">>?[[:space:]]*['\"]?${P}" && blocked=1
# edycja w miejscu
printf '%s' "$command" | grep -Eq "sed[[:space:]]+[^|;&]*-i[^|;&]*${P}" && blocked=1

if [ "$blocked" = 1 ]; then
  cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Pliki stylu sa zsynchronizowane z produkcja Delty. Napraw problem w pipelinie (a3*) albo w zrodle artykulu. Jesli zmiana stylu jest konieczna - uzgodnij z userem i zaktualizuj zapisana sume kontrolna."
  }
}
JSON
fi
exit 0
