# Admin & Database Audit

This document summarizes what the admin CRUD system writes to, what the frontend reads from, and any gaps so the **live database** is the single source of truth for content that appears on the site.

---

## ✅ Content that is fully DB-driven (admin ↔ live DB ↔ frontend)

| Admin area | Model / Source | Frontend / APIs |
|------------|----------------|-----------------|
| **Announcements** | `Announcement` | `/`, `/highlights`, `/announcements`, `/api/announcements`, `/api/highlights`, `/api/banner-announcements`, base template banner |
| **Events** (Ongoing) | `OngoingEvent` | `/sundays`, `/api/ongoing-events`, reorder UI |
| **Sunday Sermons** | `Sermon` | `/sermons`, `/sundays`, `/api/sermons`, `/api/json/sermons`, main search, archive |
| **Sermon Series** | `SermonSeries` | Sermons page grouping, filters |
| **Papers & Bulletins** | `Paper` | `/api/papers/latest` |
| **Podcast Series** | `PodcastSeries` | `/podcasts`, `/api/json/podcasts`, `/api/podcasts/*` |
| **Podcast Episodes** | `PodcastEpisode` | Same as above |
| **Gallery** | `GalleryImage` | `/gallery`, `/media`, `/yearbook`, `/api/gallery` |
| **Teaching Series** | `TeachingSeries` | `/teaching-series`, `/pastor-teaching`, `/api/teaching-series`, `/api/pastor-teaching-series` |
| **Series Sessions** | `TeachingSeriesSession` | Same as above |
| **Banner alert** | `Announcement` (show_in_banner) | Top yellow bar |
| **About page** | `SiteContent` | `/about`, `/admin/about-edit/` |
| **Community page** | `SiteContent` | `/community`, `/admin/community-edit/` |
| **Users** | `User` | Admin login, sermon “speaker” dropdown; **now has admin CRUD** (Users in “More features”) |

All of the above: **editing in admin updates the live database, and the frontend reads from that same database.**

---

## 🔧 Fixes applied (so they use the live DB)

1. **Enhanced Search** (`/api/search/sermons`, `/sermons_enhanced`)  
   - **Was:** Could fall back to `data/sermons.json` when the module loaded without an app context.  
   - **Now:** `AdvancedSearch` uses `_get_sermons()` which loads from the database (via `sermon_data_helper`) when running inside Flask; only falls back to JSON when not in the app (e.g. CLI scripts).

2. **Analytics** (`/api/analytics/overview`, `/api/analytics/trends`)  
   - **Was:** `PodcastAnalytics` always read from `data/sermons.json`.  
   - **Now:** When running inside Flask, it loads sermons from the database first; falls back to JSON only when not in the app.

3. **Users**  
   - **Was:** No admin UI to create or edit login users.  
   - **Now:** “Users” under **More features** in admin: create/edit users, set password (hashed). New users get a random password until you set a real one.

---

## 📍 Content that is **not** from the admin (external / config)

These are shown on the frontend but **do not** come from admin CRUD or the main content database:

| What | Source | Used by | Notes |
|------|--------|--------|--------|
| **Calendar events** | Google Calendar ICS (`EVENTS_ICS_URL` in config) | `/api/events`, `/events`, homepage “Events” widget, `events.js` | Managed in Google Calendar; not editable in admin. |
| **Newsletter** | RSS feed (`NEWSLETTER_FEED_URL`) | `/api/newsletter` | External feed. |
| **YouTube** | YouTube channel RSS | `/api/youtube` | Config: `YOUTUBE_CHANNEL_ID`. |
| **Bible verse** | bible-api.com | `/api/bible-verse` | External API. |
| **Mailchimp** | Mailchimp API / webhook | `/api/mailchimp`, `/api/mailchimp/latest` | Newsletter signup/content. |
| **One podcast RSS** | `PODCAST_FEEDS["cpc"]` (Anchor RSS) | `/api/podcast/cpc` (used in one place in `podcasts.html`) | Rest of podcasts page uses DB via `/api/json/podcasts`. |

So: **calendar events, newsletter, YouTube, Bible verse, Mailchimp, and the “cpc” RSS feed are not part of admin CRUD** and are intentionally external.

---

## 📂 Legacy JSON files (not used by live app for content)

These files are **not** read by the live app for the main content listed above. They may be used by scripts or docs:

- `data/sermons.json` – only as fallback when DB is unavailable (e.g. enhanced search/analytics outside Flask).
- `data/announcements.json`, `data/highlights.json`, `data/gallery.json`, `data/podcast_*.json` – used by old populate/migrate scripts, not by the running app for serving content.
- `data/cpc_newsletter_sample.json` – fallback for Mailchimp when the API fails.

The **single source of truth for live site content** is the **database** (PostgreSQL in production, SQLite locally). Use `sync_db.py` to copy production → local when developing.

---

## Summary

- **Admin CRUD** writes to the **live database** for all content types listed in the first section (including Users).
- **Frontend** reads that same database via the listed APIs and templates.
- **Enhanced Search** and **Analytics** now use the database when running in the app.
- **Calendar, newsletter, YouTube, Bible verse, Mailchimp, and one RSS feed** are external by design and are not managed in the admin CRUD.
