# CPC Web App Agent Memory (v1.0.1)

Purpose: fast context for future agents/GPTs to reduce token use and avoid re-discovery.

## Product Intent
- Primary goal: stable church content operations through Flask-Admin (sermons, announcements, podcasts, events, users).
- Current release intent: ship `v1.0.1` focused on admin workflow reliability and pagination-safe navigation.

## Architecture Snapshot
- Main app: `app.py` (routes, admin views, custom Flask-Admin behavior).
- Data models: `models.py`.
- Admin UI templates: `templates/admin/*`.
- Admin styling/interaction: `static/css/admin.css`, `templates/admin/master.html`, `static/js/admin.js`.
- IDs are globally assigned via `next_global_id()` in `models.py` (shared counter table).

## High-Risk Admin Areas
- Sermon workflow logic: `SermonView` in `app.py`.
- Announcement workflow logic: `AnnouncementView` in `app.py`.
- Podcast CRUD: `PodcastEpisodeView` in `app.py`.
- User CRUD: `UserView` in `app.py`.
- Custom bento templates:
  - `templates/admin/model/create_bento.html`
  - `templates/admin/model/edit_bento.html`
- Global admin JS overrides in `templates/admin/master.html` can unintentionally affect forms.

## Chris Issue Context (GitHub Issue #6, opened 2026-04-15)
- Requested workflow direction:
  - Sermon actions should emphasize `Save and Publish`, `Save as Draft`, `Discard Changes`.
  - After status/bulk actions, user should stay on prior list page.
  - Related Content should be more usable/clickable with richer context.
  - Content list page IDs should align to `index + 1`.
- Reported bugs include:
  - `/admin/sermon/action` internal server error on bulk actions.
  - Status changes jumping away from current page.
  - Speaker field mismatch in Add/Edit Sermon.
  - Sermon Series filter/data mismatch.
  - Announcement edit save buttons blocked by footer overlap.
  - Podcast add/edit not working.
  - User edit causing internal server error.

## Known Working Assumptions
- Dirty worktrees are common; do not revert unrelated edits.
- Preserve Flask-Admin defaults unless a deliberate override is required.
- Avoid broad template/JS changes that affect all models unless tested on multiple admin views.

## v1.0.1 Focus Boundaries
- In scope:
  - Admin reliability fixes.
  - List-page-preserving redirects.
  - Sermon/announcement/podcast/user CRUD stability.
  - UI usability fixes that block saving/editing.
- Out of scope for this patch train:
  - New feature breadth unrelated to admin stability.
  - Large redesigns of public site pages.

## Fast Triage Flow (for future agents)
1. Reproduce each admin bug locally from `/admin`.
2. Check `app.py` view hooks (`on_model_change`, `@action`, `set_status`).
3. Check corresponding template override for form/button behavior.
4. Confirm redirect keeps current `page`/filter query params.
5. Verify with create/edit/bulk/status actions before closing.

## Release Target
- Release: `v1.0.1`
- Theme: admin workflow stabilization + predictable editing flow.
