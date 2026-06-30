import os
import tempfile
import unittest
from datetime import date


_database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_database_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_database_file.name}"
os.environ["SECRET_KEY"] = "sermon-speaker-test"

from app import app, db  # noqa: E402
from models import Sermon, User  # noqa: E402


class SermonSpeakerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        cls.sermon_view = next(
            view
            for view in app.extensions["admin"][0]._views
            if getattr(view, "endpoint", None) == "sermon"
        )

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        os.unlink(_database_file.name)

    def setUp(self):
        with app.app_context():
            db.drop_all()
            db.create_all()
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["authenticated"] = True
            session["username"] = "tester"

    def _save_speaker(self, speaker_name):
        with app.test_request_context(
            "/admin/sermon/new/",
            method="POST",
            data={"speaker_name": speaker_name},
        ):
            form = self.sermon_view.create_form()
            sermon = Sermon(
                id=501,
                title="Speaker persistence test",
                date=date(2026, 6, 30),
            )
            self.sermon_view.on_model_change(form, sermon, is_created=False)
            db.session.add(sermon)
            db.session.commit()
            return sermon.id

    def test_manual_speaker_is_saved_and_prefilled(self):
        with app.app_context():
            sermon_id = self._save_speaker("Guest Preacher")
            sermon = db.session.get(Sermon, sermon_id)
            self.assertEqual(sermon.speaker, "Guest Preacher")
            self.assertIsNone(sermon.speaker_id)
            self.assertEqual(sermon.display_speaker, "Guest Preacher")

            form = self.sermon_view.edit_form(sermon)
            self.sermon_view.on_form_prefill(form, str(sermon_id))
            self.assertEqual(form.speaker_name.data, "Guest Preacher")

    def test_admin_create_form_persists_manual_speaker(self):
        response = self.client.post(
            "/admin/sermon/new/",
            data={
                "title": "Created through admin",
                "speaker_name": "Visiting Pastor",
                "date": "2026-06-30",
                "expiration_preset": "never",
            },
        )

        self.assertEqual(response.status_code, 302)
        with app.app_context():
            sermon = Sermon.query.filter_by(title="Created through admin").one()
            self.assertEqual(sermon.speaker, "Visiting Pastor")
            self.assertIsNone(sermon.speaker_id)

    def test_existing_user_name_is_linked_and_saved(self):
        with app.app_context():
            user = User(
                username="pastor",
                full_name="Pastor Example",
                password_hash="not-used-in-test",
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            sermon_id = self._save_speaker("pastor example")
            sermon = db.session.get(Sermon, sermon_id)
            self.assertEqual(sermon.speaker, "pastor example")
            self.assertEqual(sermon.speaker_id, user_id)
            self.assertEqual(sermon.display_speaker, "Pastor Example")


if __name__ == "__main__":
    unittest.main()
