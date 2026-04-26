# Punch Card #001 — Bug List 4.15.2026

**GitHub Issue**: #6  
**Status**: Open (2 of 3 completed)  
**Created by**: @Cattista  

---

## Feature Requests

### 1. Modify Sermon Workflow
- [ ] Consolidate save options to: **Save and Publish**, **Save as Draft**, **Discard Changes**
- [ ] Remove multi-sermon workflow (use SQL/bulk table grid if needed in future)
- [ ] All options should return user to **previous sermon list page**
- **Priority**: High

### 2. Make Related Content Clickable
- [ ] Each item (sermon, podcast, announcement, etc.) should be clickable
- [ ] Show detailed info: descriptions, links, images
- **Priority**: Medium

### 3. Content List Page ID Match
- [ ] Set Page ID to Page Number (i.e., Index+1)
- [ ] Ensures consistency across list pagination
- **Priority**: Low

---

## Bugs

### 4. Bulk Action Returns 500 Error
- [ ] Bulk action at `/admin/sermon/action` returns "Internal Server Error"
- [ ] Check server logs for root cause
- [ ] **Linked Sub-Issue**: #7 (menu positioning)
- **Priority**: Critical

### 5. Status Change Shouldn't Change List Page
- [ ] When changing sermon status (publish/draft/archive), stay on current list page
- [ ] Currently resets or changes pagination
- **Priority**: High

### 6. Speaker Field Uses User Table (ID, Not Name)
- [ ] Speaker field displays lowercase first name from User table
- [ ] Should use proper full name or dedicated Speaker table
- [ ] **Linked Sub-Issue**: #8 (filter/backend uses ID not name)
- **Priority**: High

### 7. Sermon Series Filter Not Attached to Series Table
- [ ] Filter only has "Luke" populated (hardcoded?)
- [ ] Should pull from SermonSeries table
- **Priority**: High

### 8. Edit Announcement Buttons Unreachable
- [ ] Save/Publish/etc buttons stuck underneath "System Online" footer
- [ ] Not clickable or visible
- **Priority**: Critical

### 9. Cannot Add/Edit Podcasts
- [ ] Add podcast functionality missing
- [ ] Edit podcast functionality missing
- [ ] Users unable to manage podcast content
- **Priority**: High

### 10. Sermon Status Toggle Style Broken
- [ ] Toggle background separated from switch graphic
- [ ] Visual alignment issue
- **Priority**: Low

### 11. Edit Users Returns 500 Error
- [ ] `/admin/users/edit` returns "Internal Server Error"
- [ ] Check server logs
- **Priority**: High

### 12. Invalid Support Contacts on Live Stream Page
- [ ] tech@cpcnewhaven.org (invalid email)
- [ ] (203) 555-0123 (placeholder phone number)
- [ ] Need correct contact info
- **Priority**: Medium

---

## Sub-Issues (Linked)

### #7 — Bulk Action Menu Positioning
**Status**: Sub-issue of #6  
- [ ] "With Selected" menu appears at **bottom of page** instead of **dropdown near button**
- [ ] Fix menu positioning to appear inline/near action button
- **Blocks**: Bug #4

### #8 — Speaker Uses ID Not Name
**Status**: Sub-issue of #6  
- [ ] Filter and backend using Speaker ID instead of joined Speaker Name
- [ ] Affects sermon display and filtering
- **Blocks**: Bug #6

### #9 — Play Button Dropdown Positioning
**Status**: Sub-issue of #6  
- [ ] Dropdowns appear **under the sermon below** instead of above/inline
- [ ] Why were separate buttons (Spotify, Apple, YouTube) removed? (design decision?)
- [ ] **Priority**: Medium

---

## Dependency Map

```
#4 (Bulk Action Error) 
  ├─ #7 (Menu Positioning)
  └─ [Unblock after fixing]

#6 (Speaker Field)
  ├─ #8 (Speaker ID vs Name)
  └─ [Blocks sermon filtering/display]

#8 (Edit Announcement Buttons)
  └─ [Unblock after layout fix]
```

---

## Quick Stats

- **Total Issues**: 9 bugs + 3 features = 12 items
- **Critical**: 2 (#4, #8)
- **High**: 5 (#5, #6, #7, #9, #11)
- **Medium**: 2 (#2, #12)
- **Low**: 2 (#3, #10)

---

## Development Notes

**Server Errors to Investigate** (500 errors):
- `/admin/sermon/action` (bulk action)
- `/admin/users/edit` (edit users)

**Database Schema Issues**:
- Sermon Series filter hardcoded or missing join to SermonSeries table
- Speaker field pulling from User table instead of Speaker table or full names

**UI/UX Issues**:
- Button/menu positioning (announcements, bulk action, play dropdown)
- Status toggle styling

---

## Next Steps

1. Review server logs for `/admin/sermon/action` and `/admin/users/edit` errors
2. Check database schema for Speaker and Series relationships
3. Audit Announcement edit form layout
4. Test bulk action menu positioning and display
5. Add podcast CRUD (not yet implemented)
