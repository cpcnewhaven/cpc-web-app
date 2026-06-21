# CPC New Haven Database Schema

## Overview

The application uses a **PostgreSQL database** hosted on Render with **10 separate tables** for different content types and system functions.

**Database Type:** PostgreSQL
**Access:** Via `DATABASE_URL` environment variable on Render
**Migration Tool:** Alembic (Flask-Migrate)

---

## Tables Overview

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `announcements` | Church announcements & events | Featured images, banner display, categories |
| `sermons` | Weekly sermons | Multi-platform links (YouTube, Spotify, Apple) |
| `podcast_episodes` | Podcast episodes | Links to series, numbered episodes |
| `podcast_series` | Teaching series/podcast series | Parent for episodes |
| `gallery_images` | Media gallery | Tags (JSON), event photos |
| `ongoing_events` | Recurring events | Sortable, categorized |
| `papers` | Teaching documents/papers | Tags (JSON), file uploads |
| `users` | Admin users | Password hashing (Werkzeug) |
| `audit_log` | Change tracking | Who did what and when |
| `global_id_counter` | Universal ID generator | Ensures unique IDs across all content |

---

## Table Details

### 1. `announcements`

Church announcements and special events.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | - | Primary key (from global counter) |
| `title` | String(200) | No | - | Announcement title |
| `description` | Text | No | - | Full description/details |
| `date_entered` | DateTime | Yes | `utcnow()` | When created |
| `active` | Boolean | Yes | `True` | Currently active? |
| `type` | String(50) | Yes | - | event, announcement, ongoing |
| `category` | String(50) | Yes | - | Categorization |
| `tag` | String(50) | Yes | - | Additional tag |
| `superfeatured` | Boolean | Yes | `False` | Extra prominent display |
| `show_in_banner` | Boolean | Yes | `False` | Show in top yellow bar |
| `archived` | Boolean | Yes | `False` | Archived status |
| `featured_image` | String(500) | Yes | - | Image URL |
| `image_display_type` | String(50) | Yes | - | poster, cover, etc. |
| `author` | String(200) | Yes | - | Who created it |

**Example Use Cases:**
- Weekly announcements
- Special events
- Parking/weather alerts (banner)
- Featured upcoming events

---

### 2. `sermons`

Weekly sermon content with multi-platform links.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | - | Primary key (from global counter) |
| `title` | String(200) | No | - | Sermon title |
| `author` | String(100) | No | - | Speaker name |
| `scripture` | String(200) | Yes | - | Bible passage reference |
| `date` | Date | No | - | Sermon date |
| `active` | Boolean | Yes | `True` | Currently active? |
| `archived` | Boolean | Yes | `False` | Archived status |
| `spotify_url` | String(500) | Yes | - | Spotify link |
| `youtube_url` | String(500) | Yes | - | YouTube link |
| `apple_podcasts_url` | String(500) | Yes | - | Apple Podcasts link |
| `podcast_thumbnail_url` | String(500) | Yes | - | Thumbnail image |

**Example Use Cases:**
- Weekly sermon archive
- Multi-platform sermon distribution
- Scripture-based sermon search

---

### 3. `podcast_episodes`

Individual podcast episodes linked to series.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | - | Primary key (from global counter) |
| `series_id` | Integer | Yes | - | Foreign key → `podcast_series.id` |
| `number` | Integer | Yes | - | Episode number |
| `title` | String(200) | No | - | Episode title |
| `link` | String(500) | Yes | - | External link |
| `listen_url` | String(500) | Yes | - | Direct audio link |
| `handout_url` | String(500) | Yes | - | Supporting materials |
| `guest` | String(100) | Yes | - | Guest speaker |
| `date_added` | Date | Yes | - | When added |
| `season` | Integer | Yes | - | Season number |
| `scripture` | String(200) | Yes | - | Bible passage |
| `podcast_thumbnail_url` | String(500) | Yes | - | Thumbnail image |

**Relationship:** `series = relationship('PodcastSeries', back_populates='episodes')`

---

### 4. `podcast_series`

Teaching series that contain multiple episodes.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | - | Primary key (from global counter) |
| `title` | String(100) | No | - | Series title |
| `description` | Text | Yes | - | Series description |

**Relationship:** `episodes = relationship('PodcastEpisode', back_populates='series')`

**Example Use Cases:**
- Multi-week teaching series
- Podcast organization
- Grouped content display

---

### 5. `gallery_images`

Media gallery for photos and images.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | - | Primary key (from global counter) |
| `name` | String(200) | Yes | - | Image name/title |
| `url` | String(500) | No | - | Image URL |
| `size` | String(50) | Yes | - | File size |
| `type` | String(50) | Yes | - | Image type |
| `tags` | JSON | Yes | - | Array of tags (e.g., `["youth", "2024"]`) |
| `event` | Boolean | Yes | `False` | Event photo? |
| `created` | DateTime | Yes | `utcnow()` | Upload date |

**Example Use Cases:**
- Event photo galleries
- Church life photos
- Searchable/filterable by tags

---

### 6. `ongoing_events`

Recurring or long-term events.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | - | Primary key (from global counter) |
| `title` | String(200) | No | - | Event title |
| `description` | Text | No | - | Event details |
| `date_entered` | DateTime | Yes | `utcnow()` | When created |
| `active` | Boolean | Yes | `True` | Currently active? |
| `archived` | Boolean | Yes | `False` | Archived status |
| `type` | String(50) | Yes | - | Event type |
| `category` | String(50) | Yes | - | Category |
| `sort_order` | Integer | Yes | `0` | Display order (lower = first) |

**Example Use Cases:**
- Weekly Bible studies
- Recurring prayer meetings
- Ongoing ministries
- Drag-and-drop reordering

---

### 7. `papers`

Teaching documents, articles, and resources.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | - | Primary key (from global counter) |
| `title` | String(200) | No | - | Document title |
| `author` | String(200) | Yes | - | Author name |
| `description` | Text | Yes | - | Description |
| `content` | Text | Yes | - | Full text content |
| `date_published` | Date | Yes | - | Publication date |
| `date_entered` | DateTime | Yes | `utcnow()` | When added |
| `category` | String(50) | Yes | - | Category |
| `tags` | JSON | Yes | - | Array of tags |
| `file_url` | String(500) | Yes | - | PDF/document URL |
| `thumbnail_url` | String(500) | Yes | - | Preview image |
| `active` | Boolean | Yes | `True` | Currently active? |

**Example Use Cases:**
- Theological papers
- Study guides
- Teaching resources
- Downloadable PDFs

---

### 8. `users`

Admin users for the CMS.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key (standard autoincrement) |
| `username` | String(80) | No | - | Unique username |
| `password_hash` | String(255) | No | - | Hashed password (Werkzeug) |
| `created_at` | DateTime | Yes | `utcnow()` | Account creation date |

**Security Features:**
- Passwords hashed using `werkzeug.security.generate_password_hash`
- `check_password()` method for authentication
- Username uniqueness enforced

---

### 9. `audit_log`

Tracks all content changes for accountability.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key (standard autoincrement) |
| `timestamp` | DateTime | No | `utcnow()` | When the action occurred (indexed) |
| `user` | String(80) | No | - | Username who made the change |
| `action` | String(20) | No | - | 'created', 'edited', 'deleted' |
| `entity_type` | String(50) | No | - | Table name (e.g., 'Announcement') |
| `entity_id` | Integer | Yes | - | ID of affected record |
| `entity_title` | String(300) | Yes | - | Human-readable title |
| `details` | Text | Yes | - | Additional info (changed fields, etc.) |

**Example Use Cases:**
- "Who deleted that announcement?"
- "When was this sermon edited?"
- Compliance and accountability
- Change history tracking

---

### 10. `global_id_counter`

Single-row table that generates universal content IDs.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | - | Always 1 (single row) |
| `next_id` | Integer | No | `1` | Next ID to assign |

**How It Works:**
1. All content tables (announcements, sermons, podcasts, etc.) get their `id` from this counter
2. IDs are unique across ALL content types: 1, 2, 3, ... 543, 544, ...
3. The `next_global_id()` function atomically increments the counter
4. Prevents ID collisions and ensures sequential ordering

**Why?** This allows:
- Universal "content ID" across all types
- Chronological ordering of all content
- Simplified cross-content features

---

## Relationships

```
podcast_series
    └── podcast_episodes (one-to-many via series_id)

global_id_counter
    └── Provides IDs to: announcements, sermons, podcast_episodes,
        podcast_series, gallery_images, ongoing_events, papers
```

---

## Database Access

### Local Development
```bash
# SQLite (default for local)
DATABASE_URL=sqlite:///cpc_newhaven.db
```

### Production (Render)
```bash
# PostgreSQL connection string (set in Render dashboard)
DATABASE_URL=postgresql://user:password@host:5432/database
```

### Connecting with SQL Clients

**Tools:** TablePlus, pgAdmin, DBeaver, psql

**Get credentials from Render:**
1. Go to your PostgreSQL service in Render dashboard
2. Click "Info" tab
3. Use the connection details or full `DATABASE_URL`

**Example connection:**
```
Host: dpg-xxxxx.oregon-postgres.render.com
Port: 5432
Database: cpc_newhaven_db
Username: cpc_newhaven_user
Password: [from Render]
```

---

## Migrations

**Tool:** Alembic (Flask-Migrate)

**Commands:**
```bash
# Create a new migration
flask db migrate -m "description of changes"

# Apply migrations
flask db upgrade

# Rollback
flask db downgrade

# View current version
flask db current
```

**Migration files:** `/migrations/versions/`

---

## Database Schema Evolution

| Date | Migration | Description |
|------|-----------|-------------|
| 2026-02-10 | `eb0dfd014d14` | Baseline migration (captured existing schema) |

---

## Security Notes

- **Passwords:** Hashed using Werkzeug's `generate_password_hash` (PBKDF2-SHA256)
- **Database URL:** Never commit `DATABASE_URL` to git - stored in `.env` and Render environment variables
- **Audit Logging:** All content changes are tracked in `audit_log` table
- **Production Auth:** Admin access requires authentication (see `DEPLOYMENT.md`)

---

## Common Queries

### Get all active sermons ordered by date
```sql
SELECT * FROM sermons
WHERE active = TRUE AND archived = FALSE
ORDER BY date DESC;
```

### Get podcast series with episode counts
```sql
SELECT ps.*, COUNT(pe.id) as episode_count
FROM podcast_series ps
LEFT JOIN podcast_episodes pe ON ps.id = pe.series_id
GROUP BY ps.id;
```

### Recent audit log entries
```sql
SELECT * FROM audit_log
ORDER BY timestamp DESC
LIMIT 50;
```

### Get all active content across types
```sql
-- Active announcements
SELECT 'announcement' as type, id, title, date_entered as date
FROM announcements WHERE active = TRUE

UNION ALL

-- Active sermons
SELECT 'sermon' as type, id, title, date as date
FROM sermons WHERE active = TRUE

ORDER BY date DESC;
```

---

## Questions?

- **App Code:** See `models.py` for SQLAlchemy model definitions
- **Database Config:** See `app.py` (lines 59-78)
- **Migrations:** See `/migrations/versions/`
- **Deployment:** See `DEPLOYMENT.md` for production setup

---

**Last Updated:** February 2026
**Database Version:** PostgreSQL 14+ (Render)
