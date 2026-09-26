import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from a11_admin_upload import parse_article_form

PAGE = """<form id="article_form">
<input name="title" value="Czy AI myśli?">
<textarea name="text">
x</textarea>
<textarea name="lead">
</textarea>
<input type="checkbox" name="published" {published}>
<select name="division"><option value="">---</option><option value="18" selected>M</option></select>
<select name="tags" multiple><option value="1" selected>a</option><option value="2">b</option></select>
<input type="submit" name="_save" value="Zapisz">
</form>"""


class ArticleFormRoundTrip(unittest.TestCase):
    def test_unpublished_stays_unpublished(self):
        fields = parse_article_form(PAGE.format(published=""))
        self.assertNotIn("published", fields)

    def test_published_stays_published(self):
        fields = parse_article_form(PAGE.format(published="checked"))
        self.assertEqual(fields["published"], "on")

    def test_values_as_browser_sends_them(self):
        fields = parse_article_form(PAGE.format(published=""))
        self.assertEqual(fields["text"], "x")
        self.assertEqual(fields["lead"], "")
        self.assertEqual(fields["division"], "18")
        self.assertEqual(fields["tags"], ["1"])
        self.assertNotIn("_save", fields)


if __name__ == "__main__":
    unittest.main()
