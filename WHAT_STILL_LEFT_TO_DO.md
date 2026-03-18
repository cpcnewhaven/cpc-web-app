# What’s Still Left to Do

Quick reference for remaining work and how to see what’s live on Render.

---

## 1. Config / content

| Item | Where | Notes |
|------|------|--------|
| **YouTube channel ID** | `config.py` | `YOUTUBE_CHANNEL_ID` is a placeholder. Replace with actual CPC New Haven channel ID (handle: @CPCNewHaven) when using YouTube features. |

---

## 2. Seeing what’s live on Render (this app’s database)

The app **cannot** connect to your Render PostgreSQL from this repo; the live DB is only reachable when the app runs on Render (or with the same `DATABASE_URL` locally).

To see what’s live:

- **Admin → Live content**  
  When you’re logged in on the deployed site (e.g. `https://cpc-new-haven.onrender.com/admin`), open **Live content** (under Content or More features). That page queries the **current app database** (on Render, that’s the Render DB) and shows:
  - Content counts (announcements, events, sermons, etc.)
  - Full list of **announcements** with status (active, banner, archived), dates, and **revision** / last updated so you can tell what’s what.

So: “what is presently live, especially announcements” = open the deployed app → Admin → **Live content**. No separate “scan” of the Render DB is possible from outside the running app.

---

## 3. Versioning (revision / last edited)

Content that supports it (starting with **Announcements**) has:

- **Revision** – integer, incremented on each save (v1, v2, …).
- **Last updated** – date/time and optional “updated by” username.

You’ll see these in:

- **Admin → Announcements** list (revision and last updated columns).
- **Admin → Live content** (announcements table with revision and last updated).

This lets editors see which version they’re looking at and who last changed it.

---

## 4. Optional / future

- Add `revision` / `updated_at` / `updated_by` to other content types (Events, Sermons, etc.) if you want the same “what is what” clarity there.
- Replace YouTube placeholder in `config.py` when you wire up YouTube.
