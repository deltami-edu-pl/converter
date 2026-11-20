import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from a10_admin_map import slugify
from articles import _detex, _match_stem


class TocToFiles(unittest.TestCase):
    QUEUE = ["01-gornicki", "02-tjz", "03-kat-o", "10-iko", "11-aktualnosci", "11-ligi", "15-bzdega"]

    def test_section_matched_by_macro_not_order(self):
        self.assertEqual(_match_stem(self.QUEUE, "tjzwspisie", "Jak dobrze być amebą", ""), "02-tjz")
        self.assertEqual(_match_stem(self.QUEUE, "liga", "", ""), "11-ligi")

    def test_iko_matched_by_title(self):
        self.assertEqual(_match_stem(self.QUEUE, "poz", "Informatyczny kącik olimpijski (142) Mexowy zbiór", "Lech Duraj"), "10-iko")

    def test_author_surname_with_polish_letters(self):
        self.assertEqual(_match_stem(self.QUEUE, "kpo", "Kąty zewnętrzne", "Bartłomiej Bzdęga"), "15-bzdega")

    def test_unknown_falls_back_to_first(self):
        self.assertEqual(_match_stem(self.QUEUE, "poz", "Coś", "Jan Kowalski"), "01-gornicki")


class Titles(unittest.TestCase):
    def test_tex_accents_and_dashes(self):
        self.assertEqual(_detex("Kto kocha Kocha, temu Ces\\`aro serce podbije"), "Kto kocha Kocha, temu Cesàro serce podbije")
        self.assertEqual(_detex("Sawayamy--Th\\'ebaulta"), "Sawayamy–Thébaulta")

    def test_slug_transliterates_like_panel(self):
        self.assertEqual(slugify("Kto kocha Kocha, temu Cesàro serce podbije"), "kto-kocha-kocha-temu-cesaro-serce-podbije")
        self.assertEqual(slugify("Zażółć gęślą jaźń Łódź"), "zazolc-gesla-jazn-lodz")


if __name__ == "__main__":
    unittest.main()
