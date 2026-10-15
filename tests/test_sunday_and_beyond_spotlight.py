import os
import tempfile
import unittest
from datetime import datetime, date
from unittest.mock import patch

_database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_database_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_database_file.name}"
os.environ["SECRET_KEY"] = "spotlight-test-key"

from app import app, db, _get_home_teaching_spotlight, sync_beyond_episodes  # noqa: E402
from models import Sermon, PodcastEpisode, PodcastEpisodeSuppression, PodcastSeries, SermonSeries  # noqa: E402


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

    def test_beyond_page_and_search_expose_playback_and_handout(self):
        with app.app_context():
            episode = db.session.get(PodcastEpisode, 101)
            episode.listen_url = 'https://files.cpcnewhaven.org/beyond/acts2.mp3?download=1'
            episode.handout_url = 'https://files.cpcnewhaven.org/beyond/acts2.pdf'
            db.session.commit()

        page = self.client.get('/podcasts')
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'Beyond the Sunday Sermon', page.data)

        beyond = self.client.get('/api/podcasts/beyond-podcast')
        self.assertEqual(beyond.status_code, 200)
        episode = beyond.json['episodes'][0]
        self.assertEqual(episode['audio_url'], 'https://files.cpcnewhaven.org/beyond/acts2.mp3?download=1')
        self.assertEqual(episode['handout_url'], 'https://files.cpcnewhaven.org/beyond/acts2.pdf')

        search = self.client.get('/api/search?type=podcasts&q=Acts+2')
        self.assertEqual(search.status_code, 200)
        result = search.json['results'][0]
        self.assertEqual(result['audio_url'], episode['audio_url'])
        self.assertEqual(result['handout_url'], episode['handout_url'])
        self.assertEqual(result['podcast_thumbnail_url'], episode['podcast_thumbnail_url'])

    def test_feed_sync_preserves_admin_edits_and_deletions(self):
        feed = [
            {'guid': 'legacy-guid', 'title': 'Acts 2 Discussion', 'guest': 'Feed guest',
             'date_added': '2026-09-27', 'link': 'https://example.org/legacy',
             'audio_url': 'https://example.org/legacy.mp3', 'podcast_thumbnail_url': ''},
            {'guid': 'new-guid', 'title': 'Acts 3 Discussion', 'guest': 'New guest',
             'date_added': '2026-10-06', 'link': 'https://example.org/new',
             'audio_url': 'https://example.org/new.mp3', 'podcast_thumbnail_url': ''},
        ]
        with app.app_context(), patch('app._get_beyond_feed_episodes', return_value=feed):
            first = sync_beyond_episodes()
            self.assertEqual(first['added'], 1)
            self.assertEqual(first['matched'], 1)
            original = db.session.get(PodcastEpisode, 101)
            self.assertEqual(original.original_id, 'legacy-guid')
            self.assertEqual(original.guest, 'Rev. Craig Luekens & Alex Gonzalez')

            imported = PodcastEpisode.query.filter_by(original_id='new-guid').one()
            self.assertEqual(imported.listen_url, 'https://example.org/new.mp3')
            _, homepage_beyond = _get_home_teaching_spotlight()
            self.assertEqual(homepage_beyond['title'], 'Acts 3 Discussion')
            self.assertFalse(homepage_beyond['is_direct_companion'])
            imported.title = 'Admin edited title'
            db.session.commit()
            self.assertEqual(sync_beyond_episodes()['added'], 0)
            self.assertEqual(imported.title, 'Admin edited title')
            public_titles = [ep['title'] for ep in self.client.get('/api/podcasts/beyond-podcast').json['episodes']]
            self.assertIn('Admin edited title', public_titles)

            db.session.add(PodcastEpisodeSuppression(original_id='new-guid'))
            db.session.delete(imported)
            db.session.commit()
            self.assertEqual(sync_beyond_episodes()['added'], 0)
            self.assertIsNone(PodcastEpisode.query.filter_by(original_id='new-guid').first())

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
