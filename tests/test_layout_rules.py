import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from a1d3_clean_tex import wrap_labeled_images
from a3a1_prepare_tex import _outside_math
from a3b_correct_html import (
    make_image_rows,
    move_captions_below_images,
    wrap_inline_exercises,
)


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class LabeledImages(unittest.TestCase):
    def test_labels_rendered_with_image(self):
        tex = "\\includegraphics[scale=.7]{a.jpg}%\n\t\\raise24pt\\llap{$A$\\kern73pt}%\n\t\\raise36pt\\llap{$\\alpha_{1}$\\kern34pt}\n\nRys. 5"
        out = wrap_labeled_images(tex)
        self.assertTrue(out.startswith("\\begin{tikzpicture}\\node[inner sep=0pt]{\\hbox{\\includegraphics"))
        self.assertIn("\\kern34pt}}};\\end{tikzpicture}", out)
        self.assertTrue(out.rstrip().endswith("Rys. 5"))

    def test_plain_image_untouched(self):
        tex = "\\includegraphics{a.jpg}\n"
        self.assertEqual(wrap_labeled_images(tex), tex)


class QuotesOutsideMath(unittest.TestCase):
    def test_double_prime_kept_in_math(self):
        out = _outside_math(",,tekst'' $A''$ \\(6''\\)", lambda t: t.replace("''", "”"))
        self.assertEqual(out, ",,tekst” $A''$ \\(6''\\)")


class CaptionsBelowImages(unittest.TestCase):
    def test_margin_label_moves_below(self):
        s = soup('<blockquote><p>Rys. 2<img src="x.png"/></p></blockquote>')
        move_captions_below_images(s)
        self.assertEqual(str(s.p), '<p><img src="x.png"/><br/>Rys. 2</p>')

    def test_text_before_image_untouched(self):
        s = soup('<p>Widać to na obrazku <img src="x.png"/></p>')
        move_captions_below_images(s)
        self.assertEqual(str(s.p), '<p>Widać to na obrazku <img src="x.png"/></p>')


class ImageRows(unittest.TestCase):
    def test_multiple_images_in_row(self):
        s = soup('<p><span><img src="a.png"/> <img src="b.png" style="max-width:200px"/></span></p>')
        make_image_rows(s)
        row = s.find("span", "image-row")
        self.assertEqual(len(row.find_all("img")), 2)
        self.assertIn("display:flex", row["style"])
        self.assertIn("max-width:min(200px, calc(50% - 12px))", row.find_all("img")[1]["style"])

    def test_margin_images_stay_stacked(self):
        s = soup('<blockquote><p><img src="a.png"/><img src="b.png"/></p></blockquote>')
        make_image_rows(s)
        self.assertIsNone(s.find("span", "image-row"))


class InlineExercises(unittest.TestCase):
    def test_solution_collapsed(self):
        s = soup(
            "<div><p><strong>Zadanie.</strong> Znajdź pola:</p>"
            '<p><img src="a.png"/></p>'
            "<p><strong>Rozwiązanie.</strong> Zakolorowane pola.</p>"
            '<p><img src="b.png"/></p>'
            "<p>Dalszy tekst.</p></div>"
        )
        wrap_inline_exercises(s)
        ex = s.find("div", "exercise")
        self.assertEqual(ex.find("header", "exercise").get_text(), "Zadanie")
        answer = ex.find("div", "answer-content")
        self.assertIn("b.png", str(answer))
        self.assertNotIn("a.png", str(answer))
        self.assertNotIn("Dalszy", str(ex))


if __name__ == "__main__":
    unittest.main()
