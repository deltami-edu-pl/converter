import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from a1d3_clean_tex import wrap_labeled_images
from a3a1_prepare_tex import _outside_math, move_closing_signature
from a3a0_clean_tex import expand_counters, stack_layout_macros, strip_klub44_logo_margins
from a3b_correct_html import (
    attach_solutions,
    caption_image_groups,
    drop_blank_paragraphs,
    open_external_links_in_new_tab,
    make_image_rows,
    resolve_numbered_refs,
    move_captions_below_images,
    wrap_inline_exercises,
)


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class LabeledImages(unittest.TestCase):
    def test_labels_rendered_with_image(self):
        tex = "\\includegraphics[scale=.7]{a.jpg}%\n\t\\raise24pt\\llap{$A$\\kern73pt}%\n\t\\raise36pt\\llap{$\\alpha_{1}$\\kern34pt}\n\nRys. 5"
        out = wrap_labeled_images(tex)
        self.assertTrue(out.startswith("\\begin{tikzpicture}\\node[inner sep=6pt]{\\hbox{\\includegraphics"))
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


class TexCleanup(unittest.TestCase):
    def test_author_counters_expanded(self):
        tex = "\\newcounter{rys}\\setcounter{rys}1 Rys. \\therys \\stepcounter{rys} Rys. \\therys $\\theta$"
        self.assertEqual(" ".join(expand_counters(tex).split()), "Rys. 1 Rys. 2 $\\theta$")

    def test_parbox_columns_stacked(self):
        tex = "\\long\\def\\dwa#1#2{\\hbox to\\hsize{\\parbox[t]{9cm}{#1}\\hfill\\parbox[t]{8cm}{#2}}}"
        self.assertEqual(stack_layout_macros(tex), "\\def\\dwa#1#2{#1\n\n#2}")

    def test_klub44_logo_margin_removed(self):
        tex = "A\\marg[-30]{\\Magenta{\\huge \\textbf{Klub 44 \\uppercase{M}}}\\vskip5pt \\includegraphics[scale=.55]{f/klub44-m.png}}{\\em B}\\marg{C}"
        self.assertEqual(strip_klub44_logo_margins(tex), "A{\\em B}\\marg{C}")

    def test_plain_macro_untouched(self):
        tex = "\\def\\xfrac#1#2{#1/#2}"
        self.assertEqual(stack_layout_macros(tex), tex)


class Solutions(unittest.TestCase):
    def test_solution_attached_to_task(self):
        s = soup(
            '<div class="zadanie"><p><strong>Zadanie 1</strong>. Wykazać.</p></div>'
            '<div class="rozwiazanie"><p><strong>Rozwiązanie 1</strong>. Szkic.</p></div>'
        )
        attach_solutions(s)
        ex = s.find("div", "exercise")
        self.assertEqual(ex.find("header", "exercise").get_text(), "Zadanie 1")
        self.assertEqual(ex.find("div", "answer-content").get_text(strip=True), "Szkic.")
        self.assertNotIn("Rozwiązanie 1", ex.get_text())

    def test_ref_to_task_shows_number(self):
        s = soup(
            '<p>zad. <a data-reference="z:a" href="#z:a">[z:a]</a></p>'
            '<div class="zadanie"><p><strong>Zadanie 2</strong>. <span id="z:a"></span>X</p></div>'
        )
        resolve_numbered_refs(s)
        self.assertEqual(s.find("a").get_text(), "2")


class Issue202612(unittest.TestCase):
    def test_signature_dropped_role_to_top(self):
        tex = "\\begin{document}Tekst.\n\n\\rightline{\\large\\em Andrzej KOMISARSKI}\n\n\\rightline{przewodniczący Jury}\n"
        out = move_closing_signature(tex)
        self.assertTrue(out.startswith("\\begin{document}\\myquote{przewodniczący Jury}Tekst."))
        self.assertNotIn("KOMISARSKI", out)

    def test_each_image_group_gets_own_caption(self):
        s = soup('<p><span><img src="a.png"/><br/>Rys. 5. A.</span><span><img src="b.png"/><br/>Rys. 6. B.</span></p>')
        caption_image_groups(s)
        caps = [c.get_text() for c in s.find_all("span", "image-caption")]
        self.assertEqual(caps, ["Rys. 5. A.", "Rys. 6. B."])
        self.assertIsNone(s.find("br"))

    def test_blank_paragraph_dropped(self):
        s = soup("<p>\xa0 \xa0</p><p>Zatem</p><p><img src='a.png'/></p>")
        drop_blank_paragraphs(s)
        self.assertEqual(len(s.find_all("p")), 2)

    def test_external_link_new_tab(self):
        s = soup('<a href="https://oeis.org/A1">x</a><a href="https://deltami.edu.pl/k/">y</a>')
        open_external_links_in_new_tab(s)
        a, b = s.find_all("a")
        self.assertEqual(a.get("target"), "_blank")
        self.assertIsNone(b.get("target"))


if __name__ == "__main__":
    unittest.main()
