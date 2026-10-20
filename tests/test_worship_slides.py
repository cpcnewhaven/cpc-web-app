"""Unit tests for worship slides workspace, bulletin parser, and slide generation."""

import json
import unittest
from unittest.mock import MagicMock, patch

from app import app, db
from worship_slides.bulletin_parser import (
    DEFAULT_BULLETIN_DOC_ID,
    DEFAULT_SLIDES_TEMPLATE_ID,
    chunk_text_into_slides,
    extract_google_id,
    extract_text_from_google_doc,
    merge_pco_with_bulletin,
    parse_bulletin_text,
)


class TestBulletinParser(unittest.TestCase):
    def test_extract_google_id(self):
        doc_url = "https://docs.google.com/document/d/1nDWJbDmvbf1PNYbHk9JMrjdihIrW2Cy9_MZoZBD-gNc/edit?usp=drive_link"
        slide_url = "https://docs.google.com/presentation/d/15zT3vmtW0ZYXYgm57qIkOAaLcNODjuNYQeur48w_oNw/edit?usp=drive_link"
        bare_id = "15zT3vmtW0ZYXYgm57qIkOAaLcNODjuNYQeur48w_oNw"

        self.assertEqual(extract_google_id(doc_url), "1nDWJbDmvbf1PNYbHk9JMrjdihIrW2Cy9_MZoZBD-gNc")
        self.assertEqual(extract_google_id(slide_url), "15zT3vmtW0ZYXYgm57qIkOAaLcNODjuNYQeur48w_oNw")
        self.assertEqual(extract_google_id(bare_id), bare_id)
        self.assertEqual(extract_google_id(""), "")

    def test_parse_bulletin_text(self):
        sample_bulletin = """
ORDER OF WORSHIP
October 18, 2026

CALL TO WORSHIP
Psalm 100:1-3
Leader: Make a joyful noise to the LORD, all the earth!
People: Serve the LORD with gladness!

HYMN OF PRAISE
Come Thou Fount of Every Blessing
Verse 1
Come, thou Fount of every blessing,
Tune my heart to sing thy grace;
Streams of mercy, never ceasing,
Call for songs of loudest praise.

Verse 2
Here I raise my Ebenezer;
Hither by thy help I'm come;

CONFESSION OF SIN
All: Most merciful God, we confess that we have sinned against you in thought, word, and deed.

SCRIPTURE READING
Romans 8:31-39
What then shall we say to these things? If God is for us, who can be against us?

SERMON
The Good Shepherd
John 10:11-18
Rev. Craig Luekens

BENEDICTION
Numbers 6:24-26
The LORD bless you and keep you.
"""
        items = parse_bulletin_text(sample_bulletin)
        self.assertGreaterEqual(len(items), 6)

        titles = [item["title"] for item in items]
        categories = {item["title"]: item["category"] for item in items}

        self.assertTrue(any("CALL TO WORSHIP" in t for t in titles))
        self.assertTrue(any("Come Thou Fount" in t for t in titles))
        self.assertTrue(any("CONFESSION" in t for t in titles))
        self.assertTrue(any("SCRIPTURE" in t for t in titles))
        self.assertTrue(any("SERMON" in t for t in titles))
        self.assertTrue(any("BENEDICTION" in t for t in titles))

        # Check song chunking into verses
        song_item = next(it for it in items if "Come Thou Fount" in it["title"])
        self.assertEqual(song_item["category"], "song")
        self.assertEqual(len(song_item["slides"]), 2)
        self.assertIn("Verse 1", song_item["slides"][0]["title"])
        self.assertIn("Verse 2", song_item["slides"][1]["title"])

    def test_extract_text_from_google_doc(self):
        mock_doc_json = {
            "title": "October 18 Bulletin",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "HEADING_1"},
                            "elements": [{"textRun": {"content": "CALL TO WORSHIP\n", "textStyle": {"bold": True}}}],
                        }
                    },
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                            "elements": [
                                {"textRun": {"content": "Leader: The Lord is in His holy temple.\n"}},
                                {"textRun": {"content": "People: Let all the earth keep silence before Him.\n"}},
                            ],
                        }
                    },
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "HEADING_1"},
                            "elements": [{"textRun": {"content": "HYMN OF PRAISE\n", "textStyle": {"bold": True}}}],
                        }
                    },
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                            "elements": [
                                {"textRun": {"content": "Holy, Holy, Holy\nVerse 1\nHoly holy holy, Lord God Almighty!\n"}},
                            ],
                        }
                    },
                ]
            },
        }

        extracted = extract_text_from_google_doc(mock_doc_json)
        self.assertIn("CALL TO WORSHIP", extracted)
        self.assertIn("Holy, Holy, Holy", extracted)

        items = parse_bulletin_text(extracted)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "CALL TO WORSHIP")
        self.assertIn("Holy, Holy, Holy", items[1]["title"])

    def test_merge_pco_with_bulletin(self):
        bulletin_items = [
            {
                "title": "Call to Worship",
                "category": "liturgy",
                "content": "Psalm 100",
                "slides": [{"title": "Call to Worship", "content": "Psalm 100"}],
            },
            {
                "title": "Hymn of Praise: Come Thou Fount",
                "category": "song",
                "content": "(Please see hymnal)",
                "slides": [{"title": "Hymn of Praise: Come Thou Fount", "content": "(Please see hymnal)"}],
            },
        ]

        pco_items = [
            {
                "title": "Come Thou Fount of Every Blessing",
                "kind": "song",
                "content": "Verse 1\nCome thou fount of every blessing\nTune my heart to sing thy grace\n\nVerse 2\nHere I raise my Ebenezer",
                "sequence": 2,
            }
        ]

        merged = merge_pco_with_bulletin(bulletin_items, pco_items)
        self.assertEqual(len(merged), 2)

        song_item = merged[1]
        self.assertTrue(song_item.get("pco_synced"))
        self.assertIn("Here I raise my Ebenezer", song_item["content"])
        self.assertEqual(len(song_item["slides"]), 2)


class TestWorshipSlidesRoutes(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def test_workspace_redirects_unauthenticated(self):
        response = self.client.get("/slides/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.location)

    def test_workspace_loads_for_staff(self):
        with self.client.session_transaction() as sess:
            sess["authenticated"] = True

        response = self.client.get("/slides/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Worship Slides Wizard", response.data)
        self.assertIn(b"15zT3vmtW0ZYXYgm57qIkOAaLcNODjuNYQeur48w_oNw", response.data)
        self.assertIn(b"1nDWJbDmvbf1PNYbHk9JMrjdihIrW2Cy9_MZoZBD-gNc", response.data)

    def test_api_parse_bulletin_text(self):
        with self.client.session_transaction() as sess:
            sess["authenticated"] = True
            sess["slides_csrf"] = "test_csrf_token_123"

        response = self.client.post(
            "/slides/api/parse-bulletin",
            headers={"X-CSRF-Token": "test_csrf_token_123"},
            json={
                "text": "CALL TO WORSHIP\nPsalm 95:1-3\n\nHYMN OF PRAISE\nDoxology\nPraise God from whom all blessings flow."
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        self.assertEqual(data["source"], "text")

    def test_api_parse_bulletin_csrf_check(self):
        with self.client.session_transaction() as sess:
            sess["authenticated"] = True
            sess["slides_csrf"] = "real_token"

        response = self.client.post(
            "/slides/api/parse-bulletin",
            headers={"X-CSRF-Token": "wrong_token"},
            json={"text": "Hello"},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
