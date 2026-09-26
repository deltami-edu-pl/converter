"""
Zakazy jako testy, nie jako prosa w regulach.

Regule w pliku z instrukcjami mozna zaprzeczyc jednym zdaniem; testu nie.
Kazdy test tutaj odpowiada jednemu zakazowi, ktory wczesniej byl tylko zapisany
slowami - i ktory zostal zlamany co najmniej raz.

Uruchomienie:  ./main.py test    albo    ./env/bin/python -m unittest discover tests
"""

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class StyleFilesAreFrozen(unittest.TestCase):
    """
    Pliki stylu sa zsynchronizowane z produkcja Delty. Lokalna zmiana rozjezdza
    artykuly z reszta serwisu, a objawia sie dopiero po wgraniu.

    Druga warstwa obok hooka PostToolUse: hook zglasza zmiane od razu po
    komendzie, ten test wylapuje ja takze wtedy, gdy powstala poza sesja.
    """

    def test_checksums_match(self):
        for name in ("article.css", "article.js"):
            path = ROOT / "static" / name
            recorded = (ROOT / "static" / f"{name}.sha256").read_text().strip()
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(
                actual, recorded,
                f"static/{name} zostal zmieniony. Jesli to swiadoma decyzja"
                f" uzgodniona z userem, zaktualizuj static/{name}.sha256."
                " Jesli nie - cofnij zmiane (git checkout -- static/) i napraw"
                " problem w pipelinie (a3*) albo w zrodle artykulu.",
            )


class NothingDeletesRemoteData(unittest.TestCase):
    """
    Ani Dropbox, ani serwis nie maja u nas sciezki usuwania. Numer da sie
    wydac bez kasowania czegokolwiek, wiec taka funkcja nie ma prawa powstac.
    """

    FORBIDDEN = (
        "files/delete", "delete_v2", "permanently_delete",
        "files/move", "files/copy_reference",
    )

    def test_no_dropbox_delete_endpoints(self):
        for path in sorted(ROOT.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            for needle in self.FORBIDDEN:
                self.assertNotIn(
                    needle, text,
                    f"{path.name} odwoluje sie do {needle!r}."
                    " Usuwanie i przenoszenie zdalnych danych jest poza zakresem"
                    " tego narzedzia.",
                )

    def test_admin_never_posts_to_change_url(self):
        """
        Upload tworzy artykuly; nadpisywanie istniejacych nie jest jego rola.
        Sam string "/change/" w pliku jest w porzadku - regex czytajacy liste
        artykulow go potrzebuje. Zakazany jest POST na taki adres.
        """
        text = (ROOT / "a11_admin_upload.py").read_text(encoding="utf-8")
        posts = re.findall(r"\.post\(\s*(.{0,90})", text, re.S)
        self.assertTrue(posts, "nie znalazlem zadnego wywolania .post - test do poprawy")
        for target in posts:
            self.assertNotIn(
                "/change/", target,
                f"POST na adres /change/ nadpisalby artykul: {target.strip()[:70]}",
            )


class DropboxWritesAreGated(unittest.TestCase):
    """
    Token zapisu byl kiedys dostepny od razu; sondowanie nim nieznanych
    endpointow obeszlo allowliste (wolalo requests.post wprost) i utworzylo
    zbedny dokument. Od tej pory zapis wymaga jawnego enable_writes().
    """

    def setUp(self):
        import dropbox_client
        self.d = dropbox_client
        self.d._writes_enabled = False

    def test_write_token_refused_by_default(self):
        with self.assertRaises(self.d.DropboxError):
            self.d.access_token(self.d.RW)

    def test_upload_refused_by_default(self):
        with self.assertRaises(self.d.DropboxError):
            self.d.upload(f"{self.d.DROPBOX_ROOT}/html.zip", b"x")

    def test_read_token_is_not_gated(self):
        """Eksperymenty naleza do tokenu RO - on nie ma scope'u zapisu."""
        try:
            self.d._creds(self.d.RO)
        except self.d.DropboxError as exc:
            self.skipTest(f"brak konfiguracji RO: {exc}")


class WriteAllowlist(unittest.TestCase):
    """Zapis wolno wykonac tylko w jednym folderze i tylko na okreslone nazwy."""

    def setUp(self):
        import dropbox_client
        self.d = dropbox_client
        self.root = dropbox_client.DROPBOX_ROOT

    def allowed(self, path: str) -> bool:
        try:
            self.d._guard_write(path)
            return True
        except self.d.DropboxError:
            return False

    def test_allows_expected_targets(self):
        self.assertTrue(self.allowed(f"{self.root}/html.zip"))
        self.assertTrue(self.allowed(f"{self.root}/2026/09/html.zip"))
        self.assertTrue(self.allowed(f"{self.root}/Delta - wydanie online.paper"))

    def test_refuses_editors_drop(self):
        """got.zip to drop redakcji - nigdy go nie nadpisujemy."""
        self.assertFalse(self.allowed(f"{self.root}/2026/09/got.zip"))

    def test_refuses_outside_root(self):
        self.assertFalse(self.allowed("/html.zip"))
        self.assertFalse(self.allowed("/Delta metriały/html.zip"))

    def test_refuses_parent_traversal(self):
        self.assertFalse(self.allowed(f"{self.root}/../inny/html.zip"))


class DisabledTexBlocks(unittest.TestCase):
    r"""\iffalse ... \fi to material wylaczony przez autora."""

    def setUp(self):
        from a1d3_clean_tex import strip_false_blocks
        self.strip = strip_false_blocks

    def norm(self, text: str) -> str:
        return " ".join(text.split())

    def test_removes_plain_block(self):
        self.assertEqual(self.norm(self.strip(r"A\iffalse B \fi C")), "A C")

    def test_keeps_else_branch(self):
        r"""W \iffalse A \else B \fi aktywna jest galaz B."""
        self.assertEqual(self.norm(self.strip(r"A\iffalse B \else K \fi C")), "A K C")

    def test_counts_nested_conditionals(self):
        r"""Nazwa polecenia TeX konczy sie na pierwszej NIE-literze: \ifnum1>0."""
        self.assertEqual(
            self.norm(self.strip(r"A\iffalse B \ifnum1>0 X \fi D \fi C")), "A C")
        self.assertEqual(
            self.norm(self.strip(r"A\iffalse B \ifx\a\b X \fi D \fi C")), "A C")

    def test_leaves_unclosed_block_alone(self):
        source = r"A\iffalse B C"
        self.assertEqual(self.strip(source), source)

    def test_leaves_stray_fi_alone(self):
        source = r"A \fi B"
        self.assertEqual(self.strip(source), source)


class SlugConvention(unittest.TestCase):
    """
    Slug jest adresem artykulu na stronie, wiec musi zgadzac sie z tym, co
    redakcja wpisuje recznie. Pary ponizej pochodza z numeru 2026-09.
    """

    CASES = {
        "Astrolabium sferyczne": "astrolabium-sferyczne",
        "Hipoteza Gilbreatha": "hipoteza-gilbreatha",
        "Kształt i opór, część 2/4 Nie tylko czapka Newtona":
            "ksztalt-i-opor-czesc-24-nie-tylko-czapka-newtona",
        "Czy AI gra w geometrię?": "czy-ai-gra-w-geometrie",
        "Trójkąty w kratkę": "trojkaty-w-kratke",
        "„Kradzież” strategii": "kradziez-strategii",
        "Aktualności: Jeden kolajder, by wszystkimi rządzić":
            "aktualnosci-jeden-kolajder-by-wszystkimi-rzadzic",
        "Niebo we wrześniu": "niebo-we-wrzesniu",
    }

    def test_matches_site(self):
        from a10_admin_map import slugify
        for title, expected in self.CASES.items():
            self.assertEqual(slugify(title), expected, f"tytul: {title!r}")

    def test_typographic_variants_collapse_to_one_slug(self):
        """
        Idempotencja uploadu opiera sie na slugu wlasnie dlatego: te same
        artykuly zapisane raz ze zrodla, raz recznie, roznia sie typografia.
        """
        from a10_admin_map import slugify
        self.assertEqual(slugify("Daj mi jedno słowo…"), slugify("Daj mi jedno słowo. . ."))
        self.assertEqual(slugify("Delta poleca: „121 deltoidów”"),
                         slugify("Delta poleca - „121 deltoidów”"))


class AdminUploadDefaultsToDryRun(unittest.TestCase):
    """Serwis nie ma zapisywalnego stagingu - domyslny bieg nie moze pisac."""

    def test_apply_defaults_to_false(self):
        import inspect
        from a11_admin_upload import admin_upload
        signature = inspect.signature(admin_upload)
        self.assertIs(signature.parameters["apply"].default, False)

    def test_publish_flag_is_never_set(self):
        """published wlacza czlowiek w panelu, nie skrypt."""
        text = (ROOT / "a11_admin_upload.py").read_text(encoding="utf-8")
        self.assertNotRegex(text, r'"published":\s*"(on|1|true)"')


if __name__ == "__main__":
    unittest.main(verbosity=2)
