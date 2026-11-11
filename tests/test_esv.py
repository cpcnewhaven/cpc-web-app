import unittest
from pathlib import Path
import esv_helper

ROOT = Path(__file__).resolve().parents[1]
BASE_HTML = (ROOT / "templates" / "base.html").read_text()


class TestESVBible(unittest.TestCase):

    def test_more_menu_includes_esv(self):
        """Verify that ESV is present in both desktop and mobile More menus."""
        # Desktop More dropdown
        self.assertIn("url_for('esv')", BASE_HTML)
        self.assertIn(">ESV</a>", BASE_HTML)

        # Mobile More sheet
        self.assertIn('class="mobile-more-link"><span>ESV</span></a>', BASE_HTML)

    def test_esv_helper_find_book(self):
        """Test book lookup by ID, full name, and common abbreviations."""
        # By ID
        self.assertEqual(esv_helper.find_book(1)["name"], "Genesis")
        self.assertEqual(esv_helper.find_book(43)["name"], "John")
        self.assertEqual(esv_helper.find_book(66)["name"], "Revelation")

        # By full name
        self.assertEqual(esv_helper.find_book("Romans")["id"], 45)
        self.assertEqual(esv_helper.find_book("romans")["id"], 45)

        # By abbreviation
        self.assertEqual(esv_helper.find_book("gen")["name"], "Genesis")
        self.assertEqual(esv_helper.find_book("jn")["name"], "John")
        self.assertEqual(esv_helper.find_book("1co")["name"], "1 Corinthians")
        self.assertEqual(esv_helper.find_book("ps")["name"], "Psalms")
        self.assertEqual(esv_helper.find_book("rev")["name"], "Revelation")

    def test_esv_helper_parse_passage_reference(self):
        """Test passage string parsing into book, chapter, and verse range."""
        # Book and chapter
        book, chap, start_v, end_v = esv_helper.parse_passage_reference("John 3")
        self.assertEqual(book["name"], "John")
        self.assertEqual(chap, 3)
        self.assertIsNone(start_v)

        # Single verse
        book, chap, start_v, end_v = esv_helper.parse_passage_reference("Romans 8:28")
        self.assertEqual(book["name"], "Romans")
        self.assertEqual(chap, 8)
        self.assertEqual(start_v, 28)

        # Numbered book with range
        book, chap, start_v, end_v = esv_helper.parse_passage_reference("1 Cor 13:4-8")
        self.assertEqual(book["name"], "1 Corinthians")
        self.assertEqual(chap, 13)
        self.assertEqual(start_v, 4)
        self.assertEqual(end_v, 8)

    def test_esv_helper_prev_and_next(self):
        """Test previous and next chapter transitions across books."""
        # First chapter of the Bible
        prev_info, next_info = esv_helper.get_prev_and_next(1, 1)
        self.assertIsNone(prev_info)
        self.assertEqual(next_info, {"book_id": 1, "book_name": "Genesis", "chapter": 2})

        # Book transition: Genesis 50 -> Exodus 1
        prev_info, next_info = esv_helper.get_prev_and_next(1, 50)
        self.assertEqual(prev_info, {"book_id": 1, "book_name": "Genesis", "chapter": 49})
        self.assertEqual(next_info, {"book_id": 2, "book_name": "Exodus", "chapter": 1})

        # Last chapter of the Bible
        prev_info, next_info = esv_helper.get_prev_and_next(66, 22)
        self.assertEqual(prev_info, {"book_id": 66, "book_name": "Revelation", "chapter": 21})
        self.assertIsNone(next_info)

    def test_esv_chapter_cached(self):
        """Test fetching chapter text from cache."""
        data = esv_helper.get_chapter_text(43, 3)
        self.assertTrue(data["success"])
        self.assertEqual(data["book"]["name"], "John")
        self.assertEqual(data["chapter"], 3)
        self.assertEqual(len(data["verses"]), 36)
        # Check John 3:16 text
        v16 = next(v for v in data["verses"] if v["verse"] == 16)
        self.assertIn("loved the world", v16["text"])


if __name__ == "__main__":
    unittest.main()

