#!/usr/bin/env python3
"""
Klient Dropboxa na dwoch tokenach o roznych uprawnieniach.

RO i RW to OSOBNE aplikacje Dropboxa. Token RO nie ma scope'u zapisu, wiec
zadny blad w kodzie nie moze nadpisac plikow na dysku - separacja jest
wymuszona po stronie Dropboxa, nie umowna. Token RW ladowany jest tylko
przez skrypty, ktore swiadomie o niego poproszą, i dodatkowo ograniczony
allowlista sciezek ponizej.
"""

import json
import os
from pathlib import Path
import requests

RO, RW = "ro", "rw"
API = "https://api.dropboxapi.com/2"
CONTENT = "https://content.dropboxapi.com/2"
TOKEN_URL = "https://api.dropbox.com/oauth2/token"

ENV_FILE = Path(".env")
RW_TOKEN_FILE = Path(".dropbox-write-token")

# Jedyny folder, ktorego potrzebujemy na Dropboksie (drop redakcji + wyniki).
# Nazwa jest doslowna, z literowka redakcji ("metrialy") - tak nazywa sie
# folder na dysku.
DROPBOX_ROOT = "/Delta metriały/TeX"

# Zapis wolno wykonac WYLACZNIE w DROPBOX_ROOT i tylko na te nazwy.
# App folder nie da sie wskazac istniejacego katalogu, wiec aplikacja zapisu
# musi byc Full Dropbox - zawezenie jest tutaj, w kodzie. Sprawdzane przed
# kazdym uploadem, patrz _guard_write.
ALLOWED_WRITE_NAMES = ("html.zip",)
ALLOWED_WRITE_PAPER = True  # dopisywanie linkow do .paper w tym folderze


class DropboxError(RuntimeError):
    pass


# Token zapisu jest zablokowany, dopoki skrypt nie poprosi o niego JAWNIE.
# Powod: sondowanie nieznanych endpointow Dropboxa tokenem RW obeszlo
# _guard_write (bo wolalo requests.post wprost) i utworzylo zbedny plik.
# Token RO nie ma scope'u zapisu, wiec eksperymenty naleza do niego.
_writes_enabled = False
_writes_reason = ""


def enable_writes(reason: str) -> None:
    """Odblokowuje token zapisu. `reason` trafia do logu, zeby bylo widac po co."""
    global _writes_enabled, _writes_reason
    _writes_enabled, _writes_reason = True, reason
    print(f"# Dropbox: zapis WLACZONY ({reason})")


def _load_env(path: Path) -> dict:
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def _creds(role: str) -> tuple[str, str, str]:
    env = {**_load_env(ENV_FILE), **os.environ}
    prefix = "DROPBOX_READ" if role == RO else "DROPBOX_WRITE"
    key = env.get(f"{prefix}_KEY", "")
    secret = env.get(f"{prefix}_SECRET", "")
    refresh = env.get(f"{prefix}_REFRESH_TOKEN", "")
    if role == RW:
        # OSOBNO trzymamy tylko REFRESH TOKEN - on jest uprawnieniem do zapisu.
        # Klucz i sekret (tozsamosc aplikacji) zostaja w .env, gdzie sa wklejane;
        # dublowanie ich tutaj powodowalo, ze stara wartosc nadpisywala nowa.
        refresh = _load_env(RW_TOKEN_FILE).get(f"{prefix}_REFRESH_TOKEN", refresh)
    missing = [n for n, v in (("KEY", key), ("SECRET", secret),
                              ("REFRESH_TOKEN", refresh)) if not v]
    if missing:
        raise DropboxError(
            f"Brak {', '.join(prefix + '_' + m for m in missing)}"
            + (f" w {RW_TOKEN_FILE}" if role == RW else f" w {ENV_FILE}")
            + " - uruchom dropbox_auth.py"
        )
    return key, secret, refresh


def access_token(role: str) -> str:
    """Dropbox wydaje tokeny 4-godzinne; refresh token wymieniamy przy kazdym uruchomieniu."""
    if role == RW and not _writes_enabled:
        raise DropboxError(
            "Token zapisu zablokowany. Skrypt musi wywolac"
            " dropbox_client.enable_writes('po co'). Do eksperymentow uzyj RO."
        )
    key, secret, refresh = _creds(role)
    r = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh,
    }, auth=(key, secret), timeout=30)
    if r.status_code != 200:
        raise DropboxError(f"Nie udalo sie odswiezyc tokenu {role}: {r.status_code} {r.text[:200]}")
    return r.json()["access_token"]


def api(role: str, endpoint: str, payload: dict | None = None) -> dict:
    r = requests.post(
        f"{API}/{endpoint}",
        headers={"Authorization": f"Bearer {access_token(role)}",
                 "Content-Type": "application/json"},
        data=json.dumps(payload if payload is not None else None),
        timeout=60,
    )
    if r.status_code != 200:
        raise DropboxError(f"{endpoint}: {r.status_code} {r.text[:300]}")
    return r.json() if r.text else {}


def download(path: str) -> bytes:
    r = requests.post(
        f"{CONTENT}/files/download",
        headers={"Authorization": f"Bearer {access_token(RO)}",
                 "Dropbox-API-Arg": json.dumps({"path": path})},
        timeout=600,
    )
    if r.status_code != 200:
        raise DropboxError(f"download {path}: {r.status_code} {r.text[:300]}")
    return r.content


def export(path: str, export_format: str = "markdown") -> bytes:
    """Tresc pliku .paper - /paper/* jest deprecated, /files/export je zastapil."""
    r = requests.post(
        f"{CONTENT}/files/export",
        headers={"Authorization": f"Bearer {access_token(RO)}",
                 "Dropbox-API-Arg": json.dumps({"path": path,
                                                "export_format": export_format})},
        timeout=120,
    )
    if r.status_code != 200:
        raise DropboxError(f"export {path}: {r.status_code} {r.text[:300]}")
    return r.content


def _guard_write(path: str) -> None:
    """Odmawia kazdego zapisu poza DROPBOX_ROOT i poza dozwolonymi nazwami."""
    # ".." odrzucamy zamiast liczyc na to, ze Dropbox potraktuje je literalnie
    if ".." in path.split("/"):
        raise DropboxError(f"Odmowa zapisu - sciezka zawiera '..': {path}")
    if not path.startswith(DROPBOX_ROOT + "/"):
        raise DropboxError(
            f"Odmowa zapisu poza {DROPBOX_ROOT}: {path}"
        )
    name = path.rsplit("/", 1)[-1]
    if name.endswith(".paper"):
        if not ALLOWED_WRITE_PAPER:
            raise DropboxError(f"Zapis do .paper wylaczony: {path}")
        return
    if name not in ALLOWED_WRITE_NAMES:
        raise DropboxError(
            f"Odmowa zapisu: {path}. Dozwolone nazwy: {ALLOWED_WRITE_NAMES} oraz *.paper"
        )


def upload(path: str, data: bytes, overwrite: bool = True) -> dict:
    _guard_write(path)
    if not _writes_enabled:
        raise DropboxError("upload bez enable_writes()")
    mode = "overwrite" if overwrite else "add"
    r = requests.post(
        f"{CONTENT}/files/upload",
        headers={"Authorization": f"Bearer {access_token(RW)}",
                 "Dropbox-API-Arg": json.dumps({"path": path, "mode": mode,
                                                "autorename": not overwrite,
                                                "mute": True}),
                 "Content-Type": "application/octet-stream"},
        data=data,
        timeout=900,
    )
    if r.status_code != 200:
        raise DropboxError(f"upload {path}: {r.status_code} {r.text[:300]}")
    return r.json()


def search(query: str, limit: int = 20) -> list[dict]:
    res = api(RO, "files/search_v2", {"query": query, "options": {"max_results": limit}})
    return [m["metadata"]["metadata"] for m in res.get("matches", [])
            if m.get("metadata", {}).get("metadata")]
