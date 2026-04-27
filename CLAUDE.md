# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Development Commands

### Run the Application
```bash
# Recommended: Smart startup with port detection
python start_app.py

# Direct start (auto-detects available port)
python app.py

# Manual port specification
flask run --port 5001
```

URLs when running locally:
- Main site: `http://localhost:PORT`
- Admin panel: `http://localhost:PORT/admin`
- Enhanced search: `http://localhost:PORT/sermons_enhanced`
- API endpoints: Various routes in `enhanced_api.py` and `json_api.py`

### Environment Setup
Create a `.env` file in the project root (gitignored):
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///cpc_newhaven.db          # SQLite for dev (default)
# DATABASE_URL=postgresql://user:pass@host/db  # Or PostgreSQL

# Optional
ANTHROPIC_API_KEY=sk-ant-...          # For Claude API features (scripture extraction)
MAILCHIMP_API_KEY=...                 # For newsletter sync
MAILCHIMP_SERVER_PREFIX=us21
MAILCHIMP_LIST_ID=...
LIVE_DATABASE_URL=postgresql://...    # For sync_db.py
```

### Database Setup
```bash
# Create tables from models
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Load sample data
python migrate_data.py

# Sync local DB with production (when DATABASE_URL is set to prod)
LIVE_DATABASE_URL='postgresql://...' python sync_db.py
```

### No Test Suite
This project has **no automated tests**. Changes should be verified manually in the browser.

### Development vs Production

**Local Development** (`FLASK_ENV=development`)
- Database: SQLite (`cpc_newhaven.db`)
- Debug mode: Enabled (auto-reload, better error pages)
- Logging: Shows request/response info
- Admin password: Not enforced (Chris's account always works)

**Production** (Render/Railway, `DATABASE_URL` set)
- Database: PostgreSQL (Render)
- Debug mode: Disabled
- Caching: Critical for performance (15-min TTL)
- Admin: Password required via Flask-Admin
- HTTPS: Enforced by Render

To test production behavior locally, set `FLASK_ENV=production` and use a PostgreSQL URL in `DATABASE_URL`.

---

## CPC New Haven – Claude Code Style Contract

Read before touching any UI, CSS, or template.

---

## Project Overview

**CPC New Haven** — a church web app built with Flask + SQLAlchemy + Flask-Admin.

- **Frontend**: public-facing site (`templates/*.html`, `static/css/style.css`)
- **Admin CRUD**: internal tool for Chris (`templates/admin/`, `static/css/admin.css`, `static/js/admin.js`)
- **Backend**: `app.py` (Flask routes, models), `enhanced_api.py`, `json_api.py`
- **DB**: PostgreSQL in production, SQLite for local dev

---

## Frontend Design System

### Theme

The site runs a **deep navy-blue glass theme** by default (`body.theme-blue`).
A light `body.theme-white` override exists — it must be fully supported when adding new components.

**Core palette (`:root`):**
```
--cpc-blue:        #0052a3
--cpc-blue-dark:   #003d7a
--cpc-blue-light:  #e8f2ff
--cpc-blue-medium: #0066cc
--bg-gradient:     linear-gradient(135deg, #004080, #003366, #00264d)
```

**Glass effects:**
```
--glass-bg:          rgba(0, 60, 130, 0.22)
--glass-bg-hover:    rgba(0, 60, 130, 0.32)
--glass-border:      rgba(0, 60, 130, 0.35)
--glass-white:       rgba(255, 255, 255, 0.22)
--glass-white-strong: rgba(255, 255, 255, 0.32)
```

**Text on dark backgrounds:**
```
--text-white:    rgba(255, 255, 255, 0.95)   ← use for headings/body on blue
--text-primary:  #1d1d1f                      ← use only on white/light surfaces
--text-secondary: #6c757d
```

### Typography

Primary font: `'Barlow'` (headings use `'Manrope'` or `'Libre Baskerville'`).
Always specify fallbacks: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`

### Glass Card Pattern (frontend)

```css
background: rgba(255, 255, 255, 0.05);   /* or rgba(0, 60, 130, 0.22) */
backdrop-filter: blur(10px);
-webkit-backdrop-filter: blur(10px);
border: 1px solid rgba(255, 255, 255, 0.1);
border-radius: 12px;
```

Hover state: nudge background opacity up + `transform: translateY(-4px)` + stronger box-shadow.

### Navigation

- Fixed top nav, glassmorphic: `rgba(0, 50, 120, 0.25)` background, `backdrop-filter: blur`
- Desktop: `.hidden lg:flex` (Tailwind utility)
- Mobile: separate `#mobileMenu` element
- Icons: Font Awesome 6 (`fa-solid`, `fa-brands`)
- **Preferred structure**: Flat top-level nav items (Home, Sundays, Sermons, Podcasts, Community, Events, Live, Resources) as direct links, with only a "More" dropdown for less common items (Give, Search, Archive, Admin)

### Tailwind Usage

Tailwind CDN is loaded in `base.html`. Use Tailwind utilities freely for layout/spacing in templates. **Do not use Tailwind for colors or backgrounds** — always use CSS variables or explicit rgba values so the theme system works.

### White Theme Support

Every new CSS rule that sets color, background, or border must have a corresponding `body.theme-white` override in `style.css` if the default is dark. Follow the existing pattern — all white-theme overrides live together in the `/* WHITE THEME - COMPREHENSIVE OVERRIDES */` section.

---

## Admin Design System

The admin uses a **completely custom dark navy theme** — no Bootstrap, no Tailwind. Everything lives in `static/css/admin.css` and `static/js/admin.js`. All admin pages have `<body class="admin-body">`.

### Admin Palette (CSS variables on `.admin-body`)

```
--admin-bg:           #0d2137      ← page background
--admin-panel:        #132f4c      ← cards, table backgrounds
--admin-panel-strong: #1a3a5c      ← table headers, panel headings
--admin-border:       #1e4976      ← all borders
--admin-text:         rgba(255, 255, 255, 0.96)
--admin-text-muted:   rgba(255, 255, 255, 0.72)
--admin-input-bg:     #132f4c
--admin-input-border: #1e4976
--cpc-blue:           #0d6efd
--cpc-blue-dark:      #0a58ca
--cpc-blue-light:     #4dabf7
--liquid-blue:        #228be6
--liquid-blue-bright: #74c0fc      ← accent text, table column headers
```

### Admin Tables — Non-Negotiable Rules

- Table background: `var(--admin-panel)` — **never white, never transparent**
- Table text: `var(--admin-text)` — **never dark/black**
- Table header cells: `color: var(--liquid-blue-bright)`, `background: var(--admin-panel-strong)`
- Row hover: `rgba(34, 139, 230, 0.08)` — subtle blue tint
- Borders: `var(--admin-border)` only
- No `background: white`, `background: #fff`, `color: #000`, `color: black` anywhere in admin

### Admin Forms

**Legacy Admin Forms** (`.admin-body` + CSS variables)
- Inputs: `background: var(--admin-input-bg)` (#132f4c), `border: 1px solid var(--admin-input-border)`, `color: var(--admin-text)`
- Labels: `color: var(--admin-text)`, `font-weight: 600`
- Use the `.admin-form-compact` grid pattern for create/edit forms
- Checkboxes render as toggle dials (see `.form-group-toggle` pattern)

**Material Design 3 Admin Forms** (newer templates using Tailwind + master.html theme)
- Inputs: Use `bg-surface-container-low` (#02132b) for better contrast and visibility
- Never use `bg-surface-container-lowest` (#000000) — too dark, poor contrast
- Focus state: `focus:bg-surface-container` (#061934) for visual feedback
- Text: `text-on-surface` (rgba(255, 255, 255, 0.95)) for legibility
- Borders: Usually `border-none`, use `shadow-inner` for depth instead

**Form Examples:**
- Date/DateTime inputs: `bg-surface-container-low focus:bg-surface-container-low`
- Text inputs: `bg-surface-container-low border-none focus:bg-surface-container-low`
- Textareas: `bg-surface-container-low focus:bg-surface-container-low`

**WYSIWYG Rich Text:** Uses Quill via `admin-wysiwyg.js` / `admin-wysiwyg.css` — dark toolbar, transparent editor bg

### Admin Buttons

```
.btn-primary  → --cpc-blue background
.btn-default  → rgba(0,50,120,0.4) background
.btn-success  → #28a745
.btn-danger   → #dc3545
```

### Admin Status Tags

Use `.admin-status-tag` with modifier classes:
- `.admin-status-published` — green
- `.admin-status-draft` — grey
- `.admin-status-featured` — blue glow
- `.admin-status-banner` — gold/yellow glow (rows with banner status get a yellow highlight)
- `.admin-status-archived` — muted grey

### Admin Panels / Cards

```css
background: var(--admin-panel);
border: 1px solid var(--admin-border);
border-radius: var(--radius);  /* 8px */
```

### Admin JS

All admin interactivity (navbar, dropdowns, modals, tabs, custom scrollbar) lives in `static/js/admin.js`. Do not add `<script>` blocks to admin templates unless it is strictly page-specific logic that cannot go in admin.js.

The custom scrollbar (`#admin-scroll-rail`) is injected dynamically by admin.js — no markup needed.

---

## Codebase Architecture

### Core Stack
- **Framework**: Flask 2.3.3 with SQLAlchemy ORM, Flask-Admin for CRUD
- **Database**: PostgreSQL (prod via Render/Railway), SQLite (local dev)
- **Frontend**: Jinja2 templates, Tailwind CDN (layout/spacing only, NOT colors), Alpine.js, vanilla JS
- **Admin**: Custom dark-themed CSS system (no Bootstrap, no Tailwind), Quill WYSIWYG for rich text
- **AI Integration**: Anthropic Claude API for content enhancement (scripture extraction, series classification)

### Key Files

| File | Purpose |
|------|---------|
| `app.py` | Flask app initialization, Flask-Admin setup, all page routes |
| `models.py` | 30+ SQLAlchemy models (Sermon, Podcast, Announcement, Event, Gallery, etc.) |
| `database.py` | SQLAlchemy instance (imported by both models and app) |
| `config.py` | Flask config, podcast feeds, event rules, timezones |
| `enhanced_api.py` | RESTful API endpoints (`/api/*`) for content retrieval |
| `json_api.py` | Secondary JSON endpoints |
| `static/css/` | `style.css` (frontend), `admin.css` (admin), `admin-wysiwyg.css` (Quill editor) |
| `static/js/admin.js` | All admin interactivity (navbar, dropdowns, modals, scrollbar) |
| `templates/base.html` | Frontend base template with nav, theme switching |
| `templates/admin/base.html` | Admin base template |
| `ingest/` | Modules for syncing content from external sources (Google Drive, Mailchimp, YouTube, events) |

### How the App Works

**Content Types** (all have dedicated models in models.py):
- **Sermon** + **SermonSeries**: Audio/video sermons with scripture references, pastors, dates
- **PodcastSeries** + **PodcastEpisode**: Distinct from sermons; fetched from RSS feeds
- **Announcement**: News/banners/events managed by Chris via admin
- **OngoingEvent**: Recurring church events (classes, groups)
- **Event**: One-off calendar events synced from Google Calendar ICS
- **GalleryImage**: Tagged photos with date metadata
- **LifeGroup**: Small group directory with metadata
- **Subpage** (with `page_key`): Custom pages (About, Community, Resources, etc.) editable in admin
- **BibleBook** + **BibleChapter**: For scripture lookups and validation

**Content Flow**:
1. Admin creates/edits content in `/admin` (Flask-Admin CRUD)
2. Content is stored in the database
3. Frontend pages call API endpoints in `enhanced_api.py` to fetch data
4. Pages render Jinja2 templates with the data
5. Alpine.js and vanilla JS handle client-side interactivity

**Admin Pages** (beyond standard CRUD):
- `/admin/quick_add_sessions` – Bulk add sermons with AI scripture extraction
- `/admin/teaching_series_overview` – Manage sermon series with reordering
- `/admin/google_drive_dashboard` – Sync media from Google Drive
- `/admin/live_content` – Toggle live broadcast features
- `/admin/banner_manage` – Feature/superfeatured announcements on homepage
- `/admin/page_editors` – Edit custom pages (About, Resources, etc.)

### Models Overview

**Core content models** (all in `models.py`):
- **Sermon** — Individual sermons with pastor, date, scripture, media links (Spotify, YouTube, Apple Podcasts)
- **SermonSeries** — Groups of sermons by topic/date range
- **PodcastSeries** + **PodcastEpisode** — Podcast episodes (different from sermons)
- **Announcement** — News, event announcements, banners (has featured/superfeatured flags)
- **Event** + **OngoingEvent** — One-off calendar events and recurring church events
- **GalleryImage** — Photos with tags and date metadata
- **LifeGroup** — Small group directory entries
- **Subpage** — Editable pages (About, Community, Resources) with `page_key` identifier
- **BibleBook** + **BibleChapter** — Scripture reference data

**Utility models:**
- **GlobalIDCounter** — Single-row table tracking next global content ID
- **TeachingSession** — Internal teaching session tracking
- **BentoBox** — Featured content container for homepage

**Design pattern**: All content models have:
- `id` — Global unique ID (pulled from `GlobalIDCounter`)
- `created_at` / `date_entered` / `date` — Timestamp
- `active` — Boolean flag for published/visible
- Various metadata (tags, categories, URLs, etc.)

### Global ID Counter
Every piece of content (across all types) gets a unique ID from `GlobalIDCounter.next_id`. This ensures IDs are globally unique and always increasing: 1, 2, 3, … 543, 544, …

### Data Sources & Integrations
- **Google Calendar**: Events synced via public ICS feed (configurable in `config.py`)
- **Podcast Feeds**: Fetched via RSS (Anchor FM, etc. — see `PODCAST_FEEDS` in config)
- **Google Drive**: Media synced via `google_drive_routes.py` and `google_drive_integration.py`
- **Mailchimp**: Newsletter integration via API or RSS (optional)
- **Claude API**: Used in `quick_add_sessions` to extract scripture and classify sermons

### Helper Scripts
- `start_app.py` – Smart Flask starter with port conflict detection
- `sync_db.py` – Sync local DB from production
- `migrate_data.py` – Load sample/bootstrap data
- `ingest/*.py` – Background modules for syncing external content (Google Drive, Mailchimp, YouTube, events)
- `populate_*.py` – Bulk-load specific content (announcements, highlights, podcasts, gallery, etc.)
- `check_*.py` – Validation/debugging utilities (check_podcasts.py, check database state, etc.)
- `setup_*.py` – One-time setup scripts (Google Drive, podcast fetcher, etc.)
- `agents/*.py` – Background sync agents for automated tasks (conflict detection, DB health checks)
- Migration scripts in `migrations/versions/` – Auto-generated by Flask-Migrate

**⚠️ DEPRECATED**: The `possiblyDELETE/` folder contains old code (old app.py, migrations, etc.). Do NOT use code from this folder — it's outdated and left for reference only.

### Caching
- Flask-Caching with SimpleCache, 15-minute default TTL
- Critical for sermon lists, podcast feeds, gallery images
- Invalidated manually when content is updated via admin

### Search System (In Progress — Phase 1 Complete)

**Architecture**: Hybrid master + subpage searches, all DB-backed via `/api/search` endpoint.

**Phase 1 Complete** ✅
- Upgraded `/api/search` in `app.py` with rich filter parameters
- Added `/api/search/meta?type=...` endpoint for filter option dropdowns
- All queries use SQLAlchemy (Render PostgreSQL), never JSON files
- **Filter params**:
  - **Sermons**: `speaker` (ID), `series_id`, `year`, `scripture_book`
  - **Podcasts**: `series_id`, `guest`, `season`
  - **Events**: `category`
  - **Gallery**: `tags` (comma-separated), `year`
- Tested: `curl "http://localhost:8000/api/search?q=grace&type=sermons"` returns paginated results

**Phases 2-3 (Planned)**
- Phase 2: Upgrade master `/search` page with advanced filter UI
- Phase 3: Update subpages (podcasts, events, gallery, sermons, teaching-series) to use `/api/search`

**Important Note**: Do NOT use `enhanced_api.py` search endpoints or `advanced_search.py` — they read from JSON files. Only use `/api/search` in `app.py`.

---

## File Structure Rules

| What | Where |
|---|---|
| Frontend styles | `static/css/style.css` |
| Admin styles | `static/css/admin.css` |
| WYSIWYG styles | `static/css/admin-wysiwyg.css` |
| Admin JS (shared) | `static/js/admin.js` |
| WYSIWYG JS | `static/js/admin-wysiwyg.js` |
| Frontend page templates | `templates/*.html` (extend `base.html`) |
| Admin templates | `templates/admin/*.html` (extend `templates/admin/base.html`) |
| Flask routes & models | `app.py` |
| API routes | `enhanced_api.py`, `json_api.py` |

**Do not create new CSS files** unless adding a genuinely isolated feature (like `admin-wysiwyg.css`). Append to the existing files instead.

---

## Adding New Features

### Add a New Content Type
1. **Model**: Define the SQLAlchemy model in `models.py` (inherit from `db.Model`)
2. **Database**: Run `db.create_all()` to create the table, or write a migration in `migrations/versions/`
3. **Admin**: Add a `ModelView` subclass in `app.py` and register it with Flask-Admin
4. **API**: Add GET/POST/PUT/DELETE endpoints in `enhanced_api.py`
5. **Frontend**: Create templates in `templates/` and link from navigation or other pages

### Add a New Page
1. **Route**: Add a route to `app.py` that renders a template
2. **Template**: Create `templates/page_name.html` extending `base.html`
3. **Data**: Fetch data via API calls or pass from the route
4. **Style**: Add page-specific styles in `{% block head %}<style>…</style>{% endblock %}`
5. **Navigation**: Add link to `templates/base.html` navigation

### Add Admin-Only Features
- Always use admin templates from `templates/admin/`
- Use CSS classes from `admin.css` (no Tailwind or Bootstrap)
- Add JS logic to `static/js/admin.js` (not page-specific `<script>` blocks)
- All form styling should use `.admin-form-compact` for consistency

### Adding API Endpoints
- **Endpoints**: Define in `enhanced_api.py` (main API) or `json_api.py` (secondary)
- **Return Format**: Always JSON with consistent structure (test in browser)
- **Database Queries**: Use SQLAlchemy query APIs, leverage `flask_sqlalchemy.get_or_404()` for safety
- **Pagination**: Use `offset` and `limit` query parameters for large lists

---

## Common Gotchas & Patterns

### Cache Invalidation
When content is updated via admin routes or API, explicitly invalidate the cache:
```python
from flask_caching import Cache
cache.delete('sermons_all')  # key must match what's cached
```
Otherwise, users will see stale data until the 15-minute TTL expires.

### WTForms Markup Patching
At the top of `app.py`, there's a monkeypatch to prevent double-escaping of HTML in forms. **Do not remove it** — it's required for Flask-Admin 1.6.x compatibility with Quill WYSIWYG editors.

### Global ID Counter
When creating new content types, use the `GlobalIDCounter` to assign IDs:
```python
from models import GlobalIDCounter
counter = db.session.query(GlobalIDCounter).filter_by(id=1).first()
new_id = counter.next_id
counter.next_id += 1
db.session.commit()
```
This ensures all IDs are globally unique across types.

### Flask-Admin Pagination
CRUD list views are paginated (e.g., 50 rows per page). To show all records, you must iterate over pages or increase `page_size` in the ModelView.

### Theme Switching
The frontend supports two themes: `body.theme-blue` (dark glass, default) and `body.theme-white` (light). **All new CSS must have corresponding overrides in the `/* WHITE THEME */` section of `style.css`**, or the white theme will break.

### Environment Variables
- `DATABASE_URL` – must be set for PostgreSQL; SQLite is the fallback
- `SECRET_KEY` – used for Flask sessions (set in `.env` or Render/Railway environment)
- `MAILCHIMP_API_KEY`, `MAILCHIMP_SERVER_PREFIX`, `MAILCHIMP_LIST_ID` – optional for newsletter sync
- `ANTHROPIC_API_KEY` – optional for Claude-powered features (scripture extraction)

### Timestamps
All datetime fields should use `datetime.utcnow` or similar UTC-aware values. Display in the correct timezone using `pytz` or JavaScript (client-side conversion).

---

## Quick Reference — Common Dev Tasks

### Clear Cache
```python
# In a Flask shell or script context
from app import app, cache
with app.app_context():
    cache.clear()
```

### Reload Frontend Without Restarting
- Browser hard refresh: `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
- Or just edit the template and reload (Flask reloads templates automatically)

### Test an API Endpoint
```bash
curl "http://localhost:5000/api/sermons?limit=5"
curl -X POST "http://localhost:5000/api/..." -H "Content-Type: application/json" -d '{"key": "value"}'
```

### Inspect Database
```bash
# Open a Flask shell
python -c "from app import app, db; app.app_context().push(); from models import *; print(db.session.query(Sermon).count())"

# Or SQLite directly
sqlite3 cpc_newhaven.db "SELECT COUNT(*) FROM sermon;"
```

### Reset Local Database
```bash
# Delete and recreate
rm cpc_newhaven.db
python -c "from app import app, db; app.app_context().push(); db.create_all()"
python migrate_data.py
```

### Check Admin Login
Admin requires `FLASK_ENV=development` or a hardcoded admin user. Default is Chris's account. Check `app.py` for admin view restrictions if adding new admin pages.

### Port Already in Use?
```bash
python start_app.py --kill-ports   # Kill processes on common ports
python start_app.py --check-ports  # Check which ports are available
```

---

## Shell Scripts

Available in the repo root for common operational tasks:

| Script | Purpose |
|--------|---------|
| `fix_ports.sh` | Kill processes on common ports (3000, 5000, 8000, etc.) |
| `sync_from_live.sh` | Sync local DB from production (reads `LIVE_DATABASE_URL` from `.env`) |
| `daily_update.sh` | Run daily syncs (podcasts, events, etc.) — use with cron |
| `weekly_analytics.sh` | Generate weekly analytics reports |
| `start_podcast_updates.sh` | Start the podcast scheduler daemon |
| `install_google_drive.sh` | Set up Google Drive integration (one-time) |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port 5000 already in use** | Run `python start_app.py --kill-ports` or `lsof -ti :5000 \| xargs kill -9` |
| **Database locked (SQLite)** | Another process is using the DB; restart Flask or check for zombie processes |
| **Stale sermon data showing** | Cache is not invalidated; run `cache.clear()` or wait 15 minutes |
| **White theme broken** | New CSS added without white-theme override; check `/* WHITE THEME */` section in `style.css` |
| **Admin page styling broken** | Check for Bootstrap/Tailwind classes in admin template; should use `admin.css` only |
| **Quill editor not showing** | Ensure `data-wysiwyg="on"` (or default) on textarea; check `admin-wysiwyg.js` is loaded |
| **Flask-Admin form looks wrong** | Check for WTForms markup double-escaping; verify monkeypatch at top of `app.py` is present |
| **API returns 404** | Check endpoint is registered in `enhanced_api.py` and blueprint is added to `app` |

---

## Hard Rules — Never Break These

1. **No white backgrounds with white or near-white text** — anywhere. This is the #1 contrast failure. Always verify text color vs background color.
2. **No `background: white` or `background: #fff`** in `admin.css` or any admin template.
3. **No black or dark text (`#000`, `#333`, `color: black`)** on dark admin backgrounds.
4. **No Bootstrap classes** in admin templates — the admin runs a fully custom CSS system. Importing Bootstrap would break it.
5. **No Tailwind classes** in admin templates — same reason.
6. **Admin and frontend are completely separate systems.** Do not mix their CSS variables, class names, or JS.
7. **Always test contrast.** Light text on dark bg (admin) and dark text on light bg (white theme) are both valid — but they must be explicitly set, never inherited by accident.
8. **Page-specific styles belong in `{% block head %}<style>…</style>{% endblock %}`** for frontend pages. Keep them scoped so they don't bleed globally.

---

## Component Patterns to Reuse

### Frontend: info/feature card
```html
<div style="background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1.25rem;">
```

### Admin: data table wrapper
```html
<div class="table-responsive">
  <table class="table">
    <thead><tr><th>…</th></tr></thead>
    <tbody><tr><td>…</td></tr></tbody>
  </table>
</div>
```

### Admin: status badge
```html
<span class="admin-status-tag admin-status-published">Published</span>
```

### Admin: page section header
```html
<div class="page-header"><h1>Section Title</h1></div>
```

---

## Known Patterns / Gotchas

- Flask-Admin list views are paginated — the CRUD list may not show all 1200 podcasts at once depending on `page_size`.
- The `announcement_direct_create.html` is a public-facing form (not admin-only) that lets users draft announcements. Style it consistently with the frontend glass theme.
- The admin scrollbar hides the native browser scrollbar via `scrollbar-width: none` — do not re-enable it on `.admin-body`.
- WYSIWYG fields use Quill. Disable it via `data-wysiwyg="off"` on a textarea if plain text is wanted.
- Inline WTForms widgets are patched with `Markup()` to prevent double-escaping — do not remove the monkeypatch at the top of `app.py`.
