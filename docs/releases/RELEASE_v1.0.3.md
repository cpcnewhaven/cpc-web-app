# Release v1.0.3

**Release Date**: May 1, 2026

## Summary
This release adds navigation improvements, media features, and May bulletin content to enhance community engagement and event participation.

## Changes

### Navigation Improvements
- **Added "Community" to primary top navigation**
  - New top-level link between "Sundays" and "More"
  - Routes to `/community` (previously `/church-directory`)
  - Consolidates Church Directory, Community Groups, Service Opportunities, New Member, and Stories
  - Also links to Media/Videos and LifeGroups from submenu
  - `/church-directory` alias maintained for backward compatibility
  - Updated all references across desktop navigation, mobile menu, and footer

- **Added "Suggest an Event" link to More dropdown**
  - Desktop: Added to the main navigation "More" menu (between Search and Archive)
  - Mobile: Added to the mobile More menu with lightbulb icon
  - Links to existing `/suggest-event` route for public event suggestions
  - Encourages community participation in event planning

### Media Features
- **Added Videos tab to Media page** (`/media`)
  - New tab alongside existing Gallery and Yearbook sections
  - Initial video: 2025 Summer Mission Trip Recap
  - Video description: Partnership recap with New City Fellowship in Atlantic City, NJ
  - Responsive YouTube embed with 16:9 aspect ratio
  - Prepared for future video additions

### May Content (via CRUD Bulk Add)
**Scripts created for automated bulk content addition:**
- `add_may_bulletin.py` — Adds May bulletin announcements and recurring events
- `add_sermon.py` — Adds upcoming Sunday sermons with speaker/scripture

**Announcements Added (6 total)**:
- Large Print Bulletin
- Children's Participation in Worship This Sunday
- Congregational Meeting (event date: May 3)
- Lost and Found
- I Heart New Haven Day (event date: June 6)
- CPC College Internship Program (expires May 3)

**OngoingEvents Added (2 total)**:
- Regular Sunday Schedule (8:30am prayer, 9:30am classes, 10:30am worship, 12pm lunch)
- Friday Pastor Drop-In Office Hours (Craig, Fridays 7:30-10:30am)

**Sermon Added**:
- Title: "The Heart of Christ"
- Scripture: Luke 19:11-40
- Speaker: Rev. Jerry Ornelas
- Date: May 3, 2026

## Files Modified
- `app.py` — Added `/community` route (alias for `/church-directory`), maintained backward compatibility
- `templates/base.html` — Added "Community" to top nav; updated all `church_directory` refs to `community`; added "Suggest an Event" to More dropdowns
- `templates/media.html` — Added Videos tab and initial mission trip video section
- `templates/community.html` — Updated page title; added submenu links to Media and LifeGroups; changed hero from "Church Directory" to "Community"
- `models.py` — No changes (used existing Announcement, OngoingEvent, Sermon models)

## Files Created
- `add_may_bulletin.py` — Reusable script for bulk announcement/event creation
- `add_sermon.py` — Reusable script for sermon creation
- `RELEASE_v1.0.3.md` — This file

## Testing Checklist

- [ ] Desktop navigation: "Community" link appears in top nav (between Sundays and More)
- [ ] Click "Community" → should load `/community` page
- [ ] Community page shows: Directory, Groups, Service, New Member, Stories sections with submenu
- [ ] Community page submenu has links to: Directory, Groups, Services, New to CPC, Stories, Media & Videos, LifeGroups
- [ ] Desktop navigation: Click "More" → verify "Suggest an Event" link appears
- [ ] Mobile navigation: Tap "More" → verify "Suggest an Event" link appears with icon
- [ ] Mobile navigation: "Community" link appears with people icon
- [ ] Click "Suggest an Event" → should load `/suggest-event` form
- [ ] Media page: `/media` → verify Videos tab present alongside Gallery and Yearbook
- [ ] Click Videos tab → should display mission trip video with title and description
- [ ] Video plays correctly on desktop and mobile (responsive)
- [ ] Admin Announcements CRUD → verify 6 new May announcements are visible
- [ ] Admin OngoingEvents CRUD → verify 2 new recurring events are visible
- [ ] Admin Sermons CRUD → verify "The Heart of Christ" sermon exists with correct speaker/scripture
- [ ] Frontend: Verify announcements display on homepage if they are featured/superfeatured
- [ ] Frontend: Verify events show in Events section if applicable

## Future Enhancements (Deferred)
- Additional videos to Media section (as they become available)
- Video metadata (duration, date uploaded) if using a custom video database
- Video search/filtering on Media page
- Categorization of videos by type (mission, worship, teaching, etc.)

## Post-Release Notes
`v1.0.3` improves community navigation and media features while adding timely May bulletin content and Sunday sermon information. New "Suggest an Event" link makes it easier for community members to participate in event planning. Videos tab on Media page creates a home for ministry recordings and mission recaps.

## Notes for Future Releases
The `add_may_bulletin.py` and `add_sermon.py` scripts provide a template for bulk content creation. For next month:
- Copy `add_may_bulletin.py` → `add_june_bulletin.py`
- Update dates and content
- Run the script to bulk-load announcements

This approach keeps the admin CRUD available for editing while enabling AI-assisted bulk data entry when needed.
