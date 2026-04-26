# Punch Card #001 — Development Checklist

**Quick reference for side-by-side terminal work**

---

## CRITICAL (Do First)

- [ ] **#4** — Bulk action `/admin/sermon/action` 500 error
- [x] **#8** — Edit Announcement buttons unreachable/under footer ✅ (Fixed: template base path)
- [ ] **#11** — Edit Users 500 error

---

## HIGH PRIORITY

- [ ] **#5** — Status change resets list page
- [ ] **#6** — Speaker field (ID vs name)
- [ ] **#7** — Bulk action menu positioning
- [ ] **#9** — Play button dropdowns under next sermon
- [ ] **#9** — Add/Edit Podcasts (not implemented)

---

## MEDIUM PRIORITY

- [ ] **#2** — Related Content clickable
- [ ] **#12** — Update support contacts (email + phone)

---

## LOW PRIORITY

- [ ] **#3** — Page ID = Page Number
- [ ] **#10** — Status toggle styling (background/switch separation)

---

## Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[x]` | Completed |
| `[P]` | In Progress |
| `[B]` | Blocked (see notes) |

---

## Notes Section

```
#4 - BLOCKED BY: Need server logs
#7 - BLOCKED BY: #4 (depends on bulk action fix)
#8 - ✅ FIXED: Changed announcement_create.html, event_create.html, teaching_series_create.html 
              to extend 'admin/master.html' instead of non-existent 'admin/model/create.html'
#9 - BLOCKED BY: Podcast CRUD not implemented
#11 - BLOCKED BY: Need server logs
```
