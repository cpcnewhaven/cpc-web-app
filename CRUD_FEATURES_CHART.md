# CRUD Features Review — CPC Web App

Review of Create, Read, Update, and Delete across admin and custom flows.  
**Legend:** ✅ Implemented and wired | ⚠️ Partial / via other flow | ❌ Not applicable (read-only or N/A)

**Versioning:** Announcements have a **revision** number (incremented on each edit), **updated_at**, and **updated_by**. Shown in Admin → Announcements list and in **Admin → Live content** so editors can see what is what. See `WHAT_STILL_LEFT_TO_DO.md` for how to see what’s live on Render.

---

## 1. Flask-Admin model views (full CRUD)

All of these use `AuthenticatedModelView` with **no** `can_create` / `can_edit` / `can_delete` overrides, so Flask-Admin provides full list/create/edit/delete by default.

| Resource | Create | Read | Update | Delete | Notes |
|----------|--------|------|--------|--------|--------|
| **Announcements** | ✅ | ✅ | ✅ | ✅ | Bulk update/delete via `/admin/bulk/announcements`. Versioning: revision, updated_at, updated_by. |
| **Events** | ✅ | ✅ | ✅ | ✅ | Custom create template; reorder via Reorder Events view |
| **Sunday Sermons** | ✅ | ✅ | ✅ | ✅ | Bulk delete/archive via `/admin/bulk/sermons` |
| **Sermon Series** | ✅ | ✅ | ✅ | ✅ | |
| **Papers & Bulletins** | ✅ | ✅ | ✅ | ✅ | Bulk delete, toggle active |
| **Podcast Series** | ✅ | ✅ | ✅ | ✅ | |
| **Podcast Episodes** | ✅ | ✅ | ✅ | ✅ | Bulk delete; thumbnail via `/api/admin/podcast-episode/<id>/thumbnail` |
| **Gallery** | ✅ | ✅ | ✅ | ✅ | Bulk delete; reorder via `/api/admin/reorder-gallery` |
| **Teaching Series** | ✅ | ✅ | ✅ | ✅ | Overview is read-only list; CRUD via Teaching Series view |
| **Series Sessions** | ✅ | ✅ | ✅ | ✅ | Reorder via Reorder Sessions view; Quick Add creates in bulk |
| **Users** | ✅ | ✅ | ✅ | ✅ | |

---

## 2. Custom / partial CRUD flows

| Feature | Create | Read | Update | Delete | Notes |
|---------|--------|------|--------|--------|--------|
| **Subpage edit** (SiteContent) | ⚠️ | ✅ | ✅ | ❌ | Create is implicit (new key on save). No delete in UI. |
| **Banner alerts** | ✅ | ✅ | ✅ | ⚠️ | Create: redirect to Announcement create with `banner=1`. Edit/expiration: `/admin/banners/<id>/expiration`. Delete: use Announcements list (delete or uncheck show_in_banner). |
| **Reorder events** | ❌ | ✅ | ✅ | ❌ | POST `/admin/events/reorder` — order only. |
| **Reorder gallery** | ❌ | ✅ | ✅ | ❌ | POST `/api/admin/reorder-gallery` — order only. |
| **Reorder sessions** | ❌ | ✅ | ✅ | ❌ | POST `/admin/teaching-series/reorder-sessions` — session order/numbers. |
| **Quick Add Sessions** | ✅ | ✅ | ❌ | ❌ | Bulk-creates sessions for a series (POST to Quick Add view). |
| **Podcast thumbnails** | ❌ | ✅ | ✅ | ❌ | List + set thumbnail per episode via API. |
| **Banner reorder** | ❌ | ✅ | ✅ | ❌ | POST `/admin/banners/reorder`. |

---

## 3. Read-only or utility views (no CRUD)

| View | Purpose |
|------|--------|
| **Dashboard** | Stats + recent content; no create/edit/delete. |
| **All content (Content Feed)** | Read-only list with links to edit (Announcement/Event edit views). |
| **Live content** | Snapshot of what’s in the DB right now: counts + full announcements list with revision/last updated. Use on Render to see live production data. |
| **Teaching Series Overview** | Read-only list; CRUD via “Teaching Series” and “Series Sessions”. |
| **Activity History** | Read-only audit log. |
| **Backup all media** | Read + download ZIP; no create/update/delete. |

---

## 4. Reference data (no admin CRUD)

| Model | In admin? | Notes |
|-------|-----------|--------|
| **BibleBook** | ❌ | Used by Sermon form (dropdown). Not managed in admin. |
| **BibleChapter** | ❌ | Used for scripture validation. Not managed in admin. |
| **GlobalIDCounter** | ❌ | Single-row counter; no UI. |
| **AuditLog** | ❌ | Append-only; view via Activity History. |

---

## 5. Summary

- **Full CRUD** (all four operations): Announcements, Events, Sermons, Sermon Series, Papers, Podcast Series, Podcast Episodes, Gallery, Teaching Series, Series Sessions, Users.
- **Partial CRUD**: SiteContent (R+U), Banners (C+R+U; D via Announcements), reorder flows (R+U for order), Quick Add (C+R), Podcast thumbnails (R+U).
- **Read-only**: Dashboard, Content Feed, Teaching Series Overview, History, Backup Gallery.
- **Not in admin**: BibleBook, BibleChapter, GlobalIDCounter, AuditLog.

All wired CRUD features are implemented in code and routes; no `can_create`/`can_edit`/`can_delete` flags are set to false on any model view. Actual behavior in production depends on database connectivity, auth, and front-end (e.g. form validation, redirects).
