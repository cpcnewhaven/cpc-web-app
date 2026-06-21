# Release Plan: v1.0.1

## Release Goal
Ship a stabilization release focused on admin workflows and issue cleanup from Chris’s 2026-04-15 bug list.

## Scope for v1.0.1
- Fix admin reliability regressions in:
  - Sermons (`/admin/sermon`)
  - Announcements (`/admin/announcement`)
  - Podcasts (`/admin/podcastepisode`)
  - Users (`/admin/user`)
- Ensure status/bulk actions preserve current list page context when possible.
- Ensure save controls are visible/clickable in edit forms.
- Keep workflow simple for sermon editing: publish, draft, discard.

## Issue Mapping (Issue #6)
- Target in this release:
  - Bulk action internal error on sermons.
  - Status change should not change list page.
  - Speaker field mismatch in sermon add/edit.
  - Sermon series filter/data mismatch.
  - Announcement edit save controls inaccessible.
  - Podcast add/edit broken.
  - User edit internal error.
- Defer unless quick win:
  - Related content richer clickable detail UX.
  - Content list page ID/index alignment.
  - Livestream support contact data cleanup.
  - Minor visual polish (status toggle styling).

## Pre-Release Verification
1. Run app locally and log in to `/admin`.
2. Verify Sermons:
  - create, save draft, publish
  - edit existing
  - bulk publish/archive/delete
  - status dropdown change
3. Verify Announcements:
  - edit form save controls visible and clickable
  - create/edit with publish and draft
4. Verify Podcasts:
  - create and edit episode
5. Verify Users:
  - open edit page and save user without 500 error
6. Verify page context:
  - from page 2+ in list, perform status/bulk action and confirm return behavior

## Tag + Push Commands
```bash
git add AGENT_MEMORY.md RELEASE_v1.0.1.md VERSION
git commit -m "Prepare v1.0.1 release docs and agent memory"
git tag -a v1.0.1 -m "v1.0.1"
git push origin <branch>
git push origin v1.0.1
```

## Post-Release Notes Template
Use this short summary:
- `v1.0.1` improves admin editing reliability and fixes key workflow regressions from Issue #6.
- Focus areas: sermon actions, status/bulk flow stability, announcement edit usability, podcast/user admin CRUD fixes.
