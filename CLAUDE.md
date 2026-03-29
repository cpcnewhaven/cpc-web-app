# CPC New Haven – Claude Code Style Contract

This file is loaded automatically on every session. Read it before touching any UI, CSS, or template.

---

## Project Overview

**CPC New Haven** — a church web app built with Flask + SQLAlchemy + Flask-Admin.

- **Frontend**: public-facing site (`templates/*.html`, `static/css/style.css`)
- **Admin CRUD**: internal tool for Chris (`templates/admin/`, `static/css/admin.css`, `static/js/admin.js`)
- **Backend**: `app.py` (Flask routes, models), `enhanced_api.py`, `json_api.py`
- **DB**: PostgreSQL in production, SQLite for local dev

---

## Frontend Design System

### Theme

The site runs a **deep navy-blue glass theme** by default (`body.theme-blue`).
A light `body.theme-white` override exists — it must be fully supported when adding new components.

**Core palette (`:root`):**
```
--cpc-blue:        #0052a3
--cpc-blue-dark:   #003d7a
--cpc-blue-light:  #e8f2ff
--cpc-blue-medium: #0066cc
--bg-gradient:     linear-gradient(135deg, #004080, #003366, #00264d)
```

**Glass effects:**
```
--glass-bg:          rgba(0, 60, 130, 0.22)
--glass-bg-hover:    rgba(0, 60, 130, 0.32)
--glass-border:      rgba(0, 60, 130, 0.35)
--glass-white:       rgba(255, 255, 255, 0.22)
--glass-white-strong: rgba(255, 255, 255, 0.32)
```

**Text on dark backgrounds:**
```
--text-white:    rgba(255, 255, 255, 0.95)   ← use for headings/body on blue
--text-primary:  #1d1d1f                      ← use only on white/light surfaces
--text-secondary: #6c757d
```

### Typography

Primary font: `'Barlow'` (headings use `'Manrope'` or `'Libre Baskerville'`).
Always specify fallbacks: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`

### Glass Card Pattern (frontend)

```css
background: rgba(255, 255, 255, 0.05);   /* or rgba(0, 60, 130, 0.22) */
backdrop-filter: blur(10px);
-webkit-backdrop-filter: blur(10px);
border: 1px solid rgba(255, 255, 255, 0.1);
border-radius: 12px;
```

Hover state: nudge background opacity up + `transform: translateY(-4px)` + stronger box-shadow.

### Navigation

- Fixed top nav, glassmorphic: `rgba(0, 50, 120, 0.25)` background, `backdrop-filter: blur`
- Desktop: `.hidden lg:flex` (Tailwind utility)
- Mobile: separate `#mobileMenu` element
- Icons: Font Awesome 6 (`fa-solid`, `fa-brands`)
- **Preferred structure**: Flat top-level nav items (Home, Sundays, Sermons, Podcasts, Community, Events, Live, Resources) as direct links, with only a "More" dropdown for less common items (Give, Search, Archive, Admin)

### Tailwind Usage

Tailwind CDN is loaded in `base.html`. Use Tailwind utilities freely for layout/spacing in templates. **Do not use Tailwind for colors or backgrounds** — always use CSS variables or explicit rgba values so the theme system works.

### White Theme Support

Every new CSS rule that sets color, background, or border must have a corresponding `body.theme-white` override in `style.css` if the default is dark. Follow the existing pattern — all white-theme overrides live together in the `/* WHITE THEME - COMPREHENSIVE OVERRIDES */` section.

---

## Admin Design System

The admin uses a **completely custom dark navy theme** — no Bootstrap, no Tailwind. Everything lives in `static/css/admin.css` and `static/js/admin.js`. All admin pages have `<body class="admin-body">`.

### Admin Palette (CSS variables on `.admin-body`)

```
--admin-bg:           #0d2137      ← page background
--admin-panel:        #132f4c      ← cards, table backgrounds
--admin-panel-strong: #1a3a5c      ← table headers, panel headings
--admin-border:       #1e4976      ← all borders
--admin-text:         rgba(255, 255, 255, 0.96)
--admin-text-muted:   rgba(255, 255, 255, 0.72)
--admin-input-bg:     #132f4c
--admin-input-border: #1e4976
--cpc-blue:           #0d6efd
--cpc-blue-dark:      #0a58ca
--cpc-blue-light:     #4dabf7
--liquid-blue:        #228be6
--liquid-blue-bright: #74c0fc      ← accent text, table column headers
```

### Admin Tables — Non-Negotiable Rules

- Table background: `var(--admin-panel)` — **never white, never transparent**
- Table text: `var(--admin-text)` — **never dark/black**
- Table header cells: `color: var(--liquid-blue-bright)`, `background: var(--admin-panel-strong)`
- Row hover: `rgba(34, 139, 230, 0.08)` — subtle blue tint
- Borders: `var(--admin-border)` only
- No `background: white`, `background: #fff`, `color: #000`, `color: black` anywhere in admin

### Admin Forms

- Inputs: `background: var(--admin-input-bg)`, `border: 1px solid var(--admin-input-border)`, `color: var(--admin-text)`
- Labels: `color: var(--admin-text)`, `font-weight: 600`
- Use the `.admin-form-compact` grid pattern for create/edit forms
- Checkboxes render as toggle dials (see `.form-group-toggle` pattern)
- WYSIWYG rich text: uses Quill via `admin-wysiwyg.js` / `admin-wysiwyg.css` — dark toolbar, transparent editor bg

### Admin Buttons

```
.btn-primary  → --cpc-blue background
.btn-default  → rgba(0,50,120,0.4) background
.btn-success  → #28a745
.btn-danger   → #dc3545
```

### Admin Status Tags

Use `.admin-status-tag` with modifier classes:
- `.admin-status-published` — green
- `.admin-status-draft` — grey
- `.admin-status-featured` — blue glow
- `.admin-status-banner` — gold/yellow glow (rows with banner status get a yellow highlight)
- `.admin-status-archived` — muted grey

### Admin Panels / Cards

```css
background: var(--admin-panel);
border: 1px solid var(--admin-border);
border-radius: var(--radius);  /* 8px */
```

### Admin JS

All admin interactivity (navbar, dropdowns, modals, tabs, custom scrollbar) lives in `static/js/admin.js`. Do not add `<script>` blocks to admin templates unless it is strictly page-specific logic that cannot go in admin.js.

The custom scrollbar (`#admin-scroll-rail`) is injected dynamically by admin.js — no markup needed.

---

## File Structure Rules

| What | Where |
|---|---|
| Frontend styles | `static/css/style.css` |
| Admin styles | `static/css/admin.css` |
| WYSIWYG styles | `static/css/admin-wysiwyg.css` |
| Admin JS (shared) | `static/js/admin.js` |
| WYSIWYG JS | `static/js/admin-wysiwyg.js` |
| Frontend page templates | `templates/*.html` (extend `base.html`) |
| Admin templates | `templates/admin/*.html` (extend `templates/admin/base.html`) |
| Flask routes & models | `app.py` |
| API routes | `enhanced_api.py`, `json_api.py` |

**Do not create new CSS files** unless adding a genuinely isolated feature (like `admin-wysiwyg.css`). Append to the existing files instead.

---

## Hard Rules — Never Break These

1. **No white backgrounds with white or near-white text** — anywhere. This is the #1 contrast failure. Always verify text color vs background color.
2. **No `background: white` or `background: #fff`** in `admin.css` or any admin template.
3. **No black or dark text (`#000`, `#333`, `color: black`)** on dark admin backgrounds.
4. **No Bootstrap classes** in admin templates — the admin runs a fully custom CSS system. Importing Bootstrap would break it.
5. **No Tailwind classes** in admin templates — same reason.
6. **Admin and frontend are completely separate systems.** Do not mix their CSS variables, class names, or JS.
7. **Always test contrast.** Light text on dark bg (admin) and dark text on light bg (white theme) are both valid — but they must be explicitly set, never inherited by accident.
8. **Page-specific styles belong in `{% block head %}<style>…</style>{% endblock %}`** for frontend pages. Keep them scoped so they don't bleed globally.

---

## Component Patterns to Reuse

### Frontend: info/feature card
```html
<div style="background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1.25rem;">
```

### Admin: data table wrapper
```html
<div class="table-responsive">
  <table class="table">
    <thead><tr><th>…</th></tr></thead>
    <tbody><tr><td>…</td></tr></tbody>
  </table>
</div>
```

### Admin: status badge
```html
<span class="admin-status-tag admin-status-published">Published</span>
```

### Admin: page section header
```html
<div class="page-header"><h1>Section Title</h1></div>
```

---

## Known Patterns / Gotchas

- Flask-Admin list views are paginated — the CRUD list may not show all 1200 podcasts at once depending on `page_size`.
- The `announcement_direct_create.html` is a public-facing form (not admin-only) that lets users draft announcements. Style it consistently with the frontend glass theme.
- The admin scrollbar hides the native browser scrollbar via `scrollbar-width: none` — do not re-enable it on `.admin-body`.
- WYSIWYG fields use Quill. Disable it via `data-wysiwyg="off"` on a textarea if plain text is wanted.
- Inline WTForms widgets are patched with `Markup()` to prevent double-escaping — do not remove the monkeypatch at the top of `app.py`.
