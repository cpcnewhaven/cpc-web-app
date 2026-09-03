# CPC New Haven - Flask Web Application

Current release marker: `v1.0.1` (see [VERSION](VERSION), [AGENT_MEMORY.md](AGENT_MEMORY.md), and [RELEASE_v1.0.1.md](RELEASE_v1.0.1.md)).

A modern Flask web application for Christ Presbyterian Church New Haven, featuring dynamic content management, sermon archives, podcast integration, and responsive design.

## Admin Editing Guide

If you are using the site as a church staff member or helper and do **not** want the technical details, start here:

- Read the plain-language guide: [docs/admin/ADMIN_USER_GUIDE.md](docs/admin/ADMIN_USER_GUIDE.md)
- Use the admin area to manage announcements, events, sermons, podcasts, gallery images, teaching series, and page content
- Changes you save in admin usually appear on the live site right away
- If you are not sure what a button does, check the guide first or ask Chris before deleting anything

This README still includes the technical setup for developers, but the user guide above is the better place to start for day-to-day editing.

## Features

- **Dynamic Content Management**: Admin interface for managing announcements, sermons, and events
- **Sermon Archives**: Searchable and filterable sermon library with multiple viewing options
- **Podcast Integration**: Multiple podcast series with episode management
- **AI-Powered Enhancement**: Automatic scripture extraction, series classification, and content tagging
- **Advanced Search**: Multi-field search with real-time suggestions and filtering
- **Analytics Dashboard**: Comprehensive analytics and insights about your content
- **Smart Port Management**: Automatic port detection and conflict resolution
- **Responsive Design**: Mobile-first design with Alpine.js for interactive components
- **API-First Architecture**: RESTful API endpoints for all content types
- **Image Gallery**: Dynamic image management with tagging and categorization
- **Deploy Verification**: Public and admin shells display the current frontend/admin build version and git hash so Render deploys are easy to confirm at a glance

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-Migrate
- **Database**: SQLite (development) / PostgreSQL (production). When `DATABASE_URL` is set (e.g. Render or local `.env`), the app stays **always connected** (pool_pre_ping + pool_recycle).
- **Frontend**: HTML5, CSS3, Alpine.js, Vanilla JavaScript
- **Admin Interface**: Flask-Admin
- **Deployment**: Ready for Heroku, Docker, or traditional hosting

## Brand Book and Theme Settings

The public site has two supported theme settings. Both are first-class brand states and every public-facing component should be checked in both modes before handoff.

- `theme-white`: the default light setting. The body carries `body.theme-white`, the background uses a pale blue-gray gradient, surfaces are white or near-white, and text should use dark ink colors such as `#1d2e42`, `#243b53`, or the light-theme `--surface-text`.
- `theme-blue`: the dark blue glass setting. The body carries `body.theme-blue`, the page background uses a deep CPC blue gradient, global text is light, and framed content may either use glass surfaces or intentional pale editorial cards with dark text when that improves scanning.

Theme state is stored in `localStorage` under `dash_theme` and is applied by `templates/base.html`. The footer and mobile controls call `window.__cpcToggleTheme`, which toggles only between `white` and `blue`.

The design-system reference lives in `CLAUDE.md` under **Frontend Design System**. Keep that file and this README aligned when theme behavior changes. The canonical public palette is:

```css
--cpc-blue: #0052a3;
--cpc-blue-dark: #003d7a;
--cpc-blue-medium: #0066cc;
--cpc-blue-light: #e8f2ff;
```

For the Highlights feature specifically, cards must visibly follow the active theme. In `theme-white`, cards sit on the light page with white surfaces, blue chips, and dark headings/body copy. In `theme-blue`, cards use dark glass surfaces, light headings/body copy, and muted blue or gold chips that remain readable on the card.

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd cpc-web-app
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database (always connected to Postgres when set)

- **On Render**: `DATABASE_URL` is set automatically; the app uses it and keeps the connection alive.
- **Local**: To use your Render Postgres (or any Postgres) from now on:
  1. Copy `.env.example` to `.env`.
  2. Set `DATABASE_URL` to your PostgreSQL URL (e.g. from Render Dashboard → your DB → Internal/External URL).
  3. Run the app; it will connect and stay connected (auto-reconnect if the server drops idle connections).

If `DATABASE_URL` is not set locally, the app falls back to SQLite.

### 5. Initialize Database

```bash
# Create database tables
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Load sample data
python migrate_data.py
```

### 6. Run the Application

#### **Smart Startup (Recommended)**
```bash
python start_app.py
```
- ✅ Automatically finds available port
- ✅ Shows all URLs (main site, admin, enhanced search)
- ✅ Handles dependencies and errors
- ✅ Provides helpful troubleshooting

#### **Direct Flask Start**
```bash
python app.py
```
- ✅ Now includes smart port detection
- ✅ Automatically finds available port
- ✅ Shows startup information

#### **Port Management**
```bash
# Check port availability
python start_app.py --check-ports

# Kill processes on common ports
python start_app.py --kill-ports

# Or use the shell script
./fix_ports.sh
```

### 7. Sync local database with production (optional)

To make your **local** database match **live** (production) so you're not developing against different data:

**Option A — One command (paste your live URL once):**

```bash
LIVE_DATABASE_URL='postgresql://user:pass@host/dbname' python sync_db.py
```

**Option B — Reusable: store URL in `.env`, then run:**

```bash
# Add to .env (do not commit; .env is gitignored):
# LIVE_DATABASE_URL=postgresql://user:pass@host/dbname

./sync_from_live.sh
```

**Option C — Full control with env vars:**

```bash
export LIVE_DATABASE_URL="postgresql://user:pass@host/dbname"
export LOCAL_DATABASE_URL="sqlite:///cpc_newhaven.db"   # optional
python sync_db.py
```

### Invite-only site feedback mode

Set `FEEDBACK_INVITE_TOKEN` to a long, private value in the environment, then send testers:

`https://cpcnewhaven.org/preview/<that-token>`

The link starts a browser session with a bottom-right floating feedback button available across the site. Testers do not need an account or a separate app. Feedback records the page, reaction type, note, and optional contact details. Authenticated admins can review it under **Admin → More → Feedback** or download `/admin/export/feedback` as CSV. Leave `FEEDBACK_INVITE_TOKEN` unset to keep feedback mode off.

The feedback button and panel are styled in `static/css/feedback.css`. Keep the launcher fixed to the bottom right, above the mobile bottom nav and audio player, and keep the panel anchored above the launcher so it does not cover the control that opened it.

**Other options:**

- `python sync_db.py --dry-run` — show what would be copied, no writes
- `python sync_db.py --export live_backup.json` — export live to JSON only

After running, your local DB will have the same announcements, sermons, podcasts, events, gallery, About/Community content, etc. as production.

The application will be available at:
- Main site: http://localhost:PORT (automatically detected)
- Admin panel: http://localhost:PORT/admin
- Enhanced search: http://localhost:PORT/sermons_enhanced

## Project Structure

```
cpc-web-app/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── config.py              # Configuration settings
├── migrate_data.py        # Sample data migration
├── requirements.txt       # Python dependencies
├── templates/             # Jinja2 templates
│   ├── base.html         # Base template
│   ├── index.html        # Homepage
│   ├── sermons.html      # Sermons page
│   ├── podcasts.html     # Podcasts page
│   └── about.html        # About page
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   ├── js/               # JavaScript files
│   └── assets/           # Images and media
└── migrations/           # Database migrations (auto-generated)
```

## API Endpoints

### Content APIs
- `GET /api/announcements` - Get all active announcements
- `GET /api/sermons` - Get all sermons
- `GET /api/podcasts/beyond-podcast` - Beyond the Sunday Sermon episodes
- `GET /api/podcasts/biblical-interpretation` - Biblical Interpretation episodes
- `GET /api/podcasts/confessional-theology` - Confessional Theology episodes
- `GET /api/podcasts/membership-seminar` - Membership Seminar episodes
- `GET /api/gallery` - Get gallery images
- `GET /api/ongoing-events` - Get ongoing events

### Page Routes
- `GET /` - Homepage
- `GET /sermons` - Sermons page
- `GET /podcasts` - Podcasts page
- `GET /about` - About page
- `GET /admin` - Admin interface

## Database Models

### Announcement
- `id` (String, Primary Key)
- `title` (String)
- `description` (Text)
- `date_entered` (DateTime)
- `active` (Boolean)
- `type` (String) - event, announcement, ongoing
- `category` (String)
- `tag` (String)
- `superfeatured` (Boolean)
- `featured_image` (String)

### Sermon
- `id` (String, Primary Key)
- `title` (String)
- `author` (String)
- `scripture` (String)
- `date` (Date)
- `spotify_url` (String)
- `youtube_url` (String)
- `apple_podcasts_url` (String)
- `podcast_thumbnail_url` (String)

### PodcastSeries
- `id` (Integer, Primary Key)
- `title` (String)
- `description` (Text)

### PodcastEpisode
- `id` (Integer, Primary Key)
- `series_id` (Integer, Foreign Key)
- `number` (Integer)
- `title` (String)
- `link` (String)
- `guest` (String)
- `date_added` (Date)
- `scripture` (String)
- `podcast_thumbnail_url` (String)

### GalleryImage
- `id` (String, Primary Key)
- `name` (String)
- `url` (String)
- `tags` (JSON)
- `event` (Boolean)
- `created` (DateTime)

### OngoingEvent
- `id` (String, Primary Key)
- `title` (String)
- `description` (Text)
- `date_entered` (DateTime)
- `active` (Boolean)
- `type` (String)
- `category` (String)

## Admin Interface

Access the admin interface at `/admin` to manage:
- Announcements and highlights
- Sermon archives
- Podcast series and episodes
- Gallery images
- Ongoing events

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///cpc_newhaven.db
```

### Production Database

For production, update the `DATABASE_URL` to use PostgreSQL:

```env
DATABASE_URL=postgresql://username:password@localhost/cpc_newhaven
```

## Deployment

### Heroku

1. Create a `Procfile`:
```
web: gunicorn app:app
```

2. Add PostgreSQL addon:
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

3. Deploy:
```bash
git push heroku main
heroku run python migrate_data.py
```

### Docker

1. Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

2. Build and run:
```bash
docker build -t cpc-web-app .
docker run -p 5000:5000 cpc-web-app
```

## Development

### Adding New Content Types

1. Create model in `models.py`
2. Add admin view in `app.py`
3. Create API endpoint
4. Update templates as needed

### Customizing Styles

Edit `static/css/style.css` to customize the appearance. The CSS is organized by component and includes responsive design.

### Adding JavaScript Functionality

Place new JavaScript files in `static/js/` and include them in templates using the `{% block scripts %}` section.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or support, please contact the development team or create an issue in the repository.

For admin editing help, start with the non-developer guide:

- [Admin User Guide](docs/admin/ADMIN_USER_GUIDE.md)

---

**Last updated**: 2026-03-27 (push access test)
