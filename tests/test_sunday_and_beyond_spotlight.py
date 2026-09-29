import os
import tempfile
import unittest
from datetime import datetime, date

_database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_database_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_database_file.name}"
os.environ["SECRET_KEY"] = "spotlight-test-key"

from app import app, db, _get_home_teaching_spotlight  # noqa: E402
from models import Sermon, PodcastEpisode, PodcastSeries, SermonSeries  # noqa: E402


class SundayAndBeyondSpotlightTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        if os.path.exists(_database_file.name):
            os.unlink(_database_file.name)

    def setUp(self):
        with app.app_context():
            db.drop_all()
            db.create_all()

            # Create Beyond podcast series
            self.beyond_series = PodcastSeries(
                id=1,
                title="Beyond the Sunday Sermon",
                description="Extended discussions with pastors on the Sunday message."
            )
            db.session.add(self.beyond_series)

            # Create Sermon series
            self.sermon_series = SermonSeries(
                id=1,
                title="Acts",
                description="The Continuing Ministry of Jesus"
            )
            db.session.add(self.sermon_series)

            # Create Beyond episode
            self.podcast_ep = PodcastEpisode(
                id=101,
                series_id=1,
                number=80,
                title="Acts 2 Discussion",
                guest="Rev. Craig Luekens & Alex Gonzalez",
                date_added=date(2026, 9, 28),
                link="https://open.spotify.com/episode/beyond80",
                listen_url="https://open.spotify.com/episode/beyond80",
                podcast_thumbnail_url="https://files.cpcnewhaven.org/beyond/art80.png"
            )
            db.session.add(self.podcast_ep)

            # Create Sermon
            self.sermon = Sermon(
                id=201,
                title="Jesus Sends the Spirit",
                speaker="Rev. Craig Luekens",
                scripture="Acts 2:1-21",
                date=date(2026, 9, 27),
                active=True,
                archived=False,
                series_id=1,
                podcast_thumbnail_url="https://files.cpcnewhaven.org/sermons/acts2.png",
                youtube_url="https://youtu.be/sampleActs2",
                spotify_url="https://open.spotify.com/episode/sampleActs2",
                apple_podcasts_url="https://podcasts.apple.com/sampleActs2",
                audio_file_url="https://files.cpcnewhaven.org/sermons/acts2.mp3",
                beyond_episode_id=101
            )
            db.session.add(self.sermon)
            db.session.commit()

        self.client = app.test_client()

    def test_spotlight_helper_with_linked_companion(self):
        """Verify helper returns correctly formatted sermon and companion podcast."""
        with app.app_context():
            sermon, beyond = _get_home_teaching_spotlight()
            self.assertIsNotNone(sermon)
            self.assertEqual(sermon['title'], "Jesus Sends the Spirit")
            self.assertEqual(sermon['speaker'], "Rev. Craig Luekens")
            self.assertEqual(sermon['scripture'], "Acts 2:1-21")
            self.assertEqual(sermon['series_title'], "Acts")
            self.assertTrue(sermon['has_linked_beyond'])
            self.assertEqual(sermon['youtube_url'], "https://youtu.be/sampleActs2")
            self.assertEqual(sermon['audio_url'], "https://files.cpcnewhaven.org/sermons/acts2.mp3")

            self.assertIsNotNone(beyond)
            self.assertEqual(beyond['title'], "Acts 2 Discussion")
            self.assertTrue(beyond['is_direct_companion'])
            self.assertIn("Craig Luekens", beyond['guest'])

    def test_homepage_renders_sunday_and_beyond_section(self):
        """Verify the homepage renders the Sunday & Beyond section and action buttons."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Header
        self.assertIn("Sunday &amp; Beyond", html)
        self.assertIn("Worship &amp; Word", html)

        # Sermon column
        self.assertIn("Jesus Sends the Spirit", html)
        self.assertIn("Acts 2:1-21", html)
        self.assertIn("Rev. Craig Luekens", html)
        self.assertIn("Watch on YouTube", html)
        self.assertIn("Listen on Spotify", html)
        self.assertIn("Play Audio", html)

        # Beyond podcast column
        self.assertIn("Acts 2 Discussion", html)
        self.assertIn("Companion Conversation to Sunday’s Sermon", html)
        self.assertIn("Listen to Discussion", html)

    def test_spotlight_api_endpoint(self):
        """Verify /api/spotlight returns JSON with sermon and beyond."""
        response = self.client.get('/api/spotlight')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('sermon', data)
        self.assertIn('beyond', data)
        self.assertEqual(data['sermon']['title'], "Jesus Sends the Spirit")
        self.assertEqual(data['beyond']['title'], "Acts 2 Discussion")
