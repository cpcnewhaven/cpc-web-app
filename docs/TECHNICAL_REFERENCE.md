# CPC New Haven Technical Reference

This document is the implementation-oriented companion to the README. It records the stack and behavior observed in the repository as of 2026-09-13. `render.yaml`, `requirements.txt`, `app.py`, `config.py`, `models.py`, and `json_api.py` are the source of truth when this document conflicts with older feature notes.

## Architecture

The application is a single Flask service:

1. Flask handles page routes, JSON routes, sessions, uploads, admin actions, and the health check.
2. Jinja templates render the public site and admin UI on the server.
3. Browser enhancements use Tailwind CSS from its CDN, Alpine.js 3.14.8, custom CSS, and vanilla JavaScript/Fetch.
4. SQLAlchemy models provide the content and admin data layer.
5. Flask-Migrate runs Alembic migrations during Render builds.
6. External ingesters fetch and normalize RSS/ICS/API data, with caching and selected local fallbacks.

There is no Node build pipeline, frontend package manifest, React/Vue/Svelte application, or bundled SPA. The frontend is template- and CDN-based.

## Runtime and dependencies

The pinned application dependencies are in [requirements.txt](../requirements.txt). The main runtime includes:

- Flask 2.3.3, Werkzeug 2.3.7, Gunicorn 21.2.0
- Flask-SQLAlchemy 3.0.5, Flask-Migrate 4.0.5, Flask-Admin 1.6.1, Flask-Caching 2.1.0
- psycopg2-binary 2.9.11 for PostgreSQL
- requests, feedparser, python-dateutil, pytz, and ics for external content
- python-dotenv for environment loading
- google-cloud-storage for optional media uploads
- anthropic and rich for the optional maintenance agents

Google Drive OAuth integration has an additional dependency set in [scripts/setup/requirements_google_drive.txt](../scripts/setup/requirements_google_drive.txt). Those packages are not currently included in the main requirements file, so the Drive integration must be installed separately before use.

## Data layer

Production requires `DATABASE_URL` and uses PostgreSQL. Local development falls back to SQLite when `DATABASE_URL` is absent. The app configures PostgreSQL connection pooling with `pool_pre_ping`, `pool_recycle=240`, a pool size of five, and up to three overflow connections.

The principal models are `Announcement`, `Sermon`, `PodcastSeries`, `PodcastEpisode`, `GalleryImage`, `OngoingEvent`, `TeachingSeries`, `TeachingSeriesSession`, `LifeGroup`, `Paper`, `SiteContent`, `SiteFeedback`, `User`, and `AuditLog`, plus Bible reference and ID-counter models. See [docs/admin/DATABASE_SCHEMA.md](admin/DATABASE_SCHEMA.md) for field-level details.

## API inventory

### Application JSON API (`app.py`)

Public GET endpoints:

```text
/api/announcements
/api/banner-announcements
/api/event-announcements
/api/highlights
/api/ongoing-events
/api/papers/latest
/api/latest-sermon
/api/sermons
/api/podcasts/beyond-podcast
/api/podcasts/biblical-interpretation
/api/podcasts/confessional-theology
/api/podcasts/membership-seminar
/api/podcast/<series_key>
/api/gallery
/api/pastor-teaching-series
/api/pastor-teaching-series/<series_id>
/api/teaching-series
/api/newsletter
/api/events
/api/youtube
/api/bible-verse
/api/mailchimp
/api/mailchimp/latest
/api/cpc-newsletter-sample
/api/events/<eid>.ics
/api/external-data
/api/search
/api/search/meta
/api/archive
```

Feedback endpoints are `POST /api/feedback` and `GET /api/feedback/<tracking_code>`. Administrative JSON actions include `GET /api/admin/last-change`, `POST /api/admin/reorder-gallery`, and `POST /api/admin/podcast-episode/<episode_id>/thumbnail`.

### Compatibility blueprint (`json_api.py`)

The compatibility blueprint exposes:

```text
/api/json/sermons
/api/json/podcasts
/api/json/podcasts/beyond-podcast
/api/json/podcasts/confessional-theology
/api/json/podcasts/biblical-interpretation
/api/json/podcasts/membership-seminar
/api/json/podcasts/what-we-believe
/api/json/podcasts/walking-with-jesus
```

These endpoints exist for older consumers and may use the sermon helper or JSON data fallback behavior. Prefer the application JSON API for new work.

## External services and data ownership

| Service | Code/config | Role |
| --- | --- | --- |
| Render | `render.yaml` | Web service, PostgreSQL, six-hour podcast cron |
| Google Calendar | `EVENTS_ICS_URL`, `app.py`, `ingest/events.py` | Public events feed and ICS export |
| YouTube | `YOUTUBE_CHANNEL_ID`, `app.py`, `ingest/youtube.py` | Channel feed and video metadata |
| Mailchimp | `MAILCHIMP_*`, `ingest/mailchimp.py` | Newsletter API/RSS, webhook, and cached latest issue |
| bible-api.com | `app.py` | Bible verse lookup |
| Podcast RSS | `PODCAST_FEEDS`, `ingest/`, `scripts/podcasts/` | Episode ingestion and sync |
| Google Drive | `google_drive_integration.py` | Optional read-only gallery synchronization |
| Google Cloud Storage | `google.cloud.storage` in `app.py` | Optional uploaded media storage |
| Anthropic | `agents/` | Optional maintenance-agent analysis; not required to serve the site |

Database-backed content managed in admin is the production source of truth. Calendar, newsletter, YouTube, Bible verse, Mailchimp, and feed-backed podcast data remain external or synchronized sources; they are not all admin CRUD records.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | Production | Flask session signing and secret material |
| `DATABASE_URL` | Production | PostgreSQL connection string; optional locally |
| `FLASK_ENV` | Recommended | Set to `production` for production behavior |
| `PORT` | Render | Render-provided bind port |
| `FEEDBACK_ENABLED` | Optional | Set to `0` to turn off public feedback (defaults to enabled for all visitors) |
| `FEEDBACK_INVITE_TOKEN` | Optional | Enables invite-only feedback session via `/preview/<token>` when `FEEDBACK_ENABLED=0` |
| `MAILCHIMP_API_KEY` | Optional | Mailchimp API authentication |
| `MAILCHIMP_SERVER_PREFIX` | Optional | Mailchimp data-center prefix, such as `us21` |
| `MAILCHIMP_LIST_ID` | Optional | Mailchimp audience/list identifier |
| `ANTHROPIC_API_KEY` | Optional | Enables the maintenance agents |
| Google OAuth/storage variables | Optional | Required only for the corresponding Google integrations; see the setup guide |

Never commit credentials, `.env`, OAuth token pickles, or production database URLs.

## Deployment contract

Render runs:

```text
Build:  pip install -r requirements.txt && flask db upgrade
Start:  gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 2 --preload
Health: /healthz
Cron:   python scripts/podcasts/fetch_and_sync.py every 6 hours
```

The web process must have `DATABASE_URL` in production. The application intentionally raises a startup error if it is missing rather than silently creating SQLite production data.

## Verification checklist

```bash
python -m unittest discover -s tests -p 'test_*.py'
python -m compileall -q app.py models.py config.py ingest agents scripts
git diff --check
```

When adding an API route, update this document and the README's API overview. When changing a third-party integration, update the relevant setup guide as well.
