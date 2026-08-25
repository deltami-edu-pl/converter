#!/usr/bin/env python3
"""
Jednorazowa autoryzacja aplikacji Dropboxa -> refresh token.

Uzycie:
    ./env/bin/python dropbox_auth.py ro
    ./env/bin/python dropbox_auth.py rw

Token RO ladowany jest do .env, RW do osobnego .dropbox-write-token, zeby
uprawnienie zapisu nie wisialo w tym samym pliku co reszta konfiguracji.
Uzywamy flow bez redirect URI (token_access_type=offline): skrypt wypisuje
link, Ty autoryzujesz w przegladarce i wklejasz kod.
"""

import sys
from pathlib import Path
import requests
from dropbox_client import ENV_FILE, RO, RW, RW_TOKEN_FILE, _load_env

AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
TOKEN_URL = "https://api.dropbox.com/oauth2/token"


def target_file(role: str) -> Path:
    """Refresh token zapisu ladujemy osobno; klucze zawsze w .env."""
    return ENV_FILE if role == RO else RW_TOKEN_FILE


def prefix(role: str) -> str:
    return "DROPBOX_READ" if role == RO else "DROPBOX_WRITE"


def ask(label: str) -> str:
    value = input(f"{label}: ").strip()
    if not value:
        sys.exit("# Przerwane - pusta wartosc")
    return value


def upsert(path: Path, values: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    for key, value in values.items():
        replaced = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                replaced = True
                break
        if not replaced:
            lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o600)


def main() -> None:
    role = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    if role not in (RO, RW):
        sys.exit("Uzycie: dropbox_auth.py [ro|rw]")

    # klucze czytamy z .env dla OBU rol - tam je wklejasz
    env = _load_env(ENV_FILE)
    key = env.get(f"{prefix(role)}_KEY") or ask(f"{prefix(role)}_KEY")
    secret = env.get(f"{prefix(role)}_SECRET") or ask(f"{prefix(role)}_SECRET")

    url = (f"{AUTH_URL}?client_id={key}&response_type=code"
           f"&token_access_type=offline")
    print()
    print("# 1. Otworz link i zatwierdz dostep:")
    print(f"#    {url}")
    print("# 2. Skopiuj kod, ktory Dropbox wyswietli.")
    print()
    # kod mozna podac argumentem: dropbox_auth.py ro <kod>
    code = sys.argv[2] if len(sys.argv) > 2 else ask("Kod autoryzacyjny")

    r = requests.post(TOKEN_URL, data={"code": code, "grant_type": "authorization_code"},
                      auth=(key, secret), timeout=30)
    if r.status_code != 200:
        sys.exit(f"# ERROR: wymiana kodu nieudana: {r.status_code} {r.text[:300]}")
    payload = r.json()
    refresh = payload.get("refresh_token")
    if not refresh:
        sys.exit("# ERROR: brak refresh_token - czy aplikacja ma token_access_type=offline?")

    scopes = payload.get("scope", "(nieznane)")
    if role == RO:
        upsert(ENV_FILE, {f"{prefix(role)}_REFRESH_TOKEN": refresh})
    else:
        # w osobnym pliku LADUJE SIE TYLKO token - bez klucza i sekretu,
        # zeby nie mogl przeslonic aktualnych wartosci z .env
        RW_TOKEN_FILE.write_text(f"{prefix(role)}_REFRESH_TOKEN={refresh}\n",
                                 encoding="utf-8")
        RW_TOKEN_FILE.chmod(0o600)
    print()
    print(f"# Zapisano do {target_file(role)} (chmod 600)")
    print(f"# Nadane scope'y: {scopes}")
    if role == RO and ("content.write" in scopes or "files.content.write" in scopes):
        print("# !!! UWAGA: token RO ma scope ZAPISU - to lamie separacje uprawnien.")
        print("#     Utworz osobna aplikacje bez files.content.write.")


if __name__ == "__main__":
    main()
