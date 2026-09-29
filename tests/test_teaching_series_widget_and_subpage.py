import os
import tempfile
import unittest
from datetime import date

_database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_database_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_database_file.name}"
os.environ["SECRET_KEY"] = "teaching-series-test-key"

from app import app, db, SUBPAGE_CONFIGS  # noqa: E402
from models import Sermon, SermonSeries, SiteContent  # noqa: E402
from sermon_data_helper import get_sermon_helper  # noqa: E402


class TeachingSeriesWidgetAndSubpageTestCase(unittest.TestCase):
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

            # Set SiteContent for teaching series
            db.session.add(SiteContent(key='current_teaching_series_title', value='Acts'))
            db.session.add(SiteContent(key='previous_teaching_series_title', value='Luke'))
            db.session.add(SiteContent(key='current_teaching_series_subtitle', value='The Sunday Sermon Podcast'))

            # Set SermonSeries
            acts_series = SermonSeries(id=54, title='Acts', active=True, sort_order=0)
            luke_series = SermonSeries(id=30, title='Luke', active=True, sort_order=1)
            db.session.add(acts_series)
            db.session.add(luke_series)

            # Add sermons
            db.session.add(Sermon(
                id=1,
                title='Jesus Ascends',
                scripture='Acts 1:1-11',
                date=date(2026, 9, 13),
                active=True,
                archived=False,
                series_id=54
            ))
            db.session.add(Sermon(
                id=2,
                title='Jesus Sends the Spirit',
                scripture='Acts 2:1-21',
                date=date(2026, 9, 27),
                active=True,
                archived=False,
                series_id=54
            ))
            db.session.add(Sermon(
                id=3,
                title='The Emmaus Road',
                scripture='Luke 24:13-35',
                date=date(2026, 8, 30),
                active=True,
                archived=False,
                series_id=30
            ))
            db.session.commit()

        self.client = app.test_client()

    def test_sidebar_widget_renders_acts(self):
        """Verify the Current Teaching Series widget on pages renders Acts and links to teaching-series."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn('Current Teaching Series', html)
        self.assertIn('Acts', html)
        self.assertIn('The Sunday Sermon Podcast', html)
        self.assertIn('/teaching-series?q=Acts', html)

    def test_subpage_editor_homepage_defaults(self):
        """Verify the subpage config for homepage includes Acts as current and Luke as previous."""
        hp_config = SUBPAGE_CONFIGS['homepage']
        keys = {item[0]: item[2] for item in hp_config['keys']}
        self.assertEqual(keys.get('current_teaching_series_title'), 'Acts')
        self.assertEqual(keys.get('previous_teaching_series_title'), 'Luke')

    def test_teaching_series_subpage_renders_acts_and_luke(self):
        """Verify /teaching-series subpage displays current series Acts and previous Luke."""
        response = self.client.get('/teaching-series')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn('Current Preaching Series', html)
        self.assertIn('Acts', html)
        self.assertIn('Previous series:', html)
        self.assertIn('Luke', html)
        self.assertIn('/sermons?series=54', html)

    def test_today_at_cpc_fallback(self):
        """Verify display page uses current series Acts."""
        response = self.client.get('/display')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Teaching series:', html)
        self.assertIn('Acts', html)

    def test_latest_book_chapter_helper(self):
        """Verify sermon helper finds latest chapter for Acts."""
        with app.app_context():
            helper = get_sermon_helper()
            acts_chapter = helper.get_latest_book_chapter('Acts')
            self.assertIsNotNone(acts_chapter)
            self.assertEqual(acts_chapter['latest_by_date']['chapter'], 2)

            luke_chapter = helper.get_latest_luke_chapter()
            self.assertIsNotNone(luke_chapter)
            self.assertEqual(luke_chapter['latest_by_date']['chapter'], 24)
