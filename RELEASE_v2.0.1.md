# Release: v2.0.1

## Overview
Admin dashboard refinement release focused on fixing navigation errors and improving modal routing consistency.

## Changes

### Bug Fixes
- **Fix admin "Create New Entry" modal announcement link** — Corrected `/admin/announcement/new/` → `/admin/announcement/create/` to match custom route configuration
- **Fix admin create form 404 errors** — Corrected template base paths for announcement and bento forms
- **Fix teaching series new-entry link** — Added missing trailing slash to `/admin/teachingseries/new/` for URL consistency

### Impact
- Users can now successfully create new announcements from the admin dashboard modal
- All "Create New Entry" modal links now route to correct endpoints
- Dashboard navigation is more reliable and consistent

## Commits
- `61e6830` Fix admin create form 404 errors: correct template base paths
- `8fdaddd` Fix admin create announcement 404: correct modal link from /new/ to /create/
- `14c5d9e` Add trailing slash to teachingseries new-entry link for consistency

## Verification
- [x] Announcement creation works from modal
- [x] All modal links have consistent trailing slashes
- [x] Admin routes match Flask-Admin configuration
