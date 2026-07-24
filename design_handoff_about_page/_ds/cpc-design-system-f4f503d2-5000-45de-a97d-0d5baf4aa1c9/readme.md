# CPC Design System

Design system for **Christ Presbyterian Church (CPC) New Haven** — a Flask web application with a public-facing marketing/ministry site and an internal Flask-Admin CMS.

## Sources
- GitHub: [cpcnewhaven/cpc-web-app](https://github.com/cpcnewhaven/cpc-web-app) — the live Flask app. This system was built by reading `templates/base.html`, `templates/index.html`, `templates/events.html`, `templates/admin/dashboard.html`, `static/css/style.css`, `static/css/admin.css`, and the `design_handoff_*` folders in that repo.
- Uploaded stylesheets: `uploads/style.css` (public site, 5700+ lines) and `uploads/admin.css` (admin CMS, custom dark theme).
- Written design-philosophy notes provided alongside the upload (glassmorphic navy theme, admin dark theme, typography, content use-cases).

Explore the repo further for anything this system doesn't cover yet — full page templates for Sermons, Podcasts, Teaching Series, Gallery, and every Flask-Admin CRUD screen live there in `templates/` and `templates/admin/`.

## Two products, two visual systems
1. **Public site** — deep navy-blue glassmorphic theme (default, `body.theme-blue`) with a light alternative (`body.theme-white`). Marketing pages: home, sermons, podcasts, events, gallery, about, live stream, give.
2. **Admin CMS** (`/admin`) — a completely separate, deliberately non-Bootstrap/non-Tailwind-for-color dark theme (`#0d2137` background) for Flask-Admin CRUD screens (announcements, sermons, podcasts, gallery) plus a newer Tailwind+MD3-token dashboard shell (`templates/admin/dashboard.html`, `master.html`). **Never mix the two admin palettes with the public glass tokens.**

## Components
Public site (`components/core`, `components/feedback`, `components/forms`, `components/content`, `components/navigation`):
- **Button** — primary/secondary/glass CTA button
- **GlassCard** — the base frosted-glass surface
- **Badge** — content-type pill (event/announcement/ongoing/upcoming)
- **Chip** — filter/category toggle
- **FormField** — glass input/select/textarea
- **EventCard** — event/announcement listing card
- **NavBar** — floating glass top navigation

Admin CMS (`components/admin`):
- **AdminButton** — primary/default/success/danger CRUD button
- **AdminStatusTag** — published/draft/featured/banner/archived pill
- **AdminPanel** — dark bordered panel/well
- **AdminTable** — CRUD list table
- **AdminFormField** — dark input + toggle switch
- **AdminModal** — confirm/edit dialog

### Intentional additions
None of the above were invented — every one maps to a CSS class already defined in `uploads/style.css` / `uploads/admin.css` (`.btn`, `.glass-card`, `.chip`, `.evt-card`, `.admin-status-tag`, `.panel`, `.table`, `.form-control` + toggle, `.modal`). No Toast, Tooltip, Avatar, or Tabs component was added since the source doesn't define one.

## UI Kits
- `ui_kits/public-site/` — click-through recreation of the homepage + Events page, with a light/dark theme toggle.
- `ui_kits/admin-dashboard/` — click-through recreation of the admin System Dashboard + an Announcements CRUD list with a "new entry" modal.

## Content fundamentals
- **Voice**: warm, plain, pastoral — "Everyone is truly welcomed," "You are welcome here," "Come as you are." Second person direct address ("Plan your first visit," "Join us"). No slang, no forced enthusiasm, no emoji.
- **Casing**: sentence case for body copy and buttons ("Plan a Visit," "Watch Live"); Title Case for nav labels and section headings.
- **Tone**: theologically grounded but accessible — pull quotes lean confessional ("we are more loved in Christ than we can ever dare to hope"), while UI copy (buttons, nav, admin) stays functional and short.
- **Admin copy** is more clipped and operational ("Initiate New Entry," "Broadcast News," "Initialize Workflow") — a CMS-operator register, distinct from the pastoral public voice.
- Emoji are not used anywhere in the source CSS/templates reviewed.

## Visual foundations
- **Color**: one brand blue (`#0052a3`) plus a navy gradient background (`#004080 → #003366 → #00264d`) for the public site; the admin CMS uses an unrelated darker MD3-flavored blue palette (`#0d2137` bg, `#0d6efd`/`#228be6` accents) — treat them as two palettes, never blend.
- **Type**: Barlow (body, -0.01em tracking, 15px base) + Manrope (headings, 500–800 weight, tight 1.2–1.3 leading) + Libre Baskerville (serif, pull-quotes only — never UI chrome).
- **Backgrounds**: full-bleed diagonal gradients (135deg) behind glass content; photographic hero banners (fading crossfade slideshow on the homepage) with a dark-to-transparent-to-dark gradient overlay for text legibility. No illustration or pattern textures — photography + gradient + glass only.
- **Glassmorphism is the core motif**: `backdrop-filter: blur(8–40px)` + translucent white/blue fills + a 1px translucent border on almost every card, nav, dropdown, and modal. Admin surfaces use lighter blur (8–12px) and are less transparent (more opaque navy) than public-site glass.
- **Animation**: minimal and functional — `translateY(-2px to -4px)` lifts on card/button hover, opacity crossfades for hero slideshows and modals (`0.2–0.3s ease`), a `pulse` scale/opacity keyframe for live-status dots, a slow marquee scroll for the footer ticker. No bounce, no elastic easing.
- **Hover states**: cards lift + deepen shadow; buttons darken (primary) or invert fill (secondary outline → filled); glass surfaces brighten slightly (`--glass-bg` → `--glass-bg-hover`).
- **Press/active states**: not explicitly defined in source CSS beyond `:hover`/`:focus-visible` — treat press as an instant, no-transition darken if needed.
- **Borders & shadows**: borders are 1px, translucent (`rgba(255,255,255,0.1–0.2)` on dark, `rgba(0,0,0,0.1)` on light) rather than solid brand-colored lines. Shadows are soft and diffuse (`0 4–8px 30px rgba(0,0,0,0.1–0.3)`), no hard drop shadows, no colored-left-border card accents.
- **Corner radii**: 6/12/16/24px scale (`--radius-sm/md/lg/xl`), plus full pills for badges/chips/status tags.
- **Transparency & blur**: used everywhere content sits over a gradient or photo — nav, dropdowns, cards, modals, dashboard sidebars, the footer ticker. Rarely used on plain white backgrounds (light theme swaps blur+translucency for near-opaque white).
- **Imagery**: warm-toned documentary photography of the congregation, building, and events (no stock-model gloss, no black & white, no heavy grain) layered under dark gradient overlays for text contrast.

## Iconography
- **Font Awesome 6** (`fa-solid`, `fa-brands`) via CDN (`cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1`) — the only icon system in the codebase. No custom SVG icon set, no PNG icon sprites were found.
- No emoji used as icons anywhere in the reviewed templates/CSS.
- No unicode glyphs as icons, except a literal `×` close button and `☰`/hamburger character in a couple of legacy spots — Font Awesome is the standard everywhere else.
- **Load Font Awesome via CDN `<link>`** in any page using icons (see the UI kit `index.html` files for the exact tag) — it isn't bundled into `_ds_bundle.js`.

## Logo / brand mark
**No logo file exists in the reviewed source.** The real site references a logo by external URL (`https://cpcnewhaven.org/assets/CPC_LOGO_24.png`, inverted to white via CSS filter) and a favicon hosted at `files.cpcnewhaven.org` — neither is a file in the `cpc-web-app` repo, and no logo was uploaded to this project. Every place a mark would go (`NavBar`, `thumbnail.html`, `Wordmark` guideline card) renders the church name as plain type instead. **If you have the actual logo file, please attach it and I'll wire it into `NavBar`, the UI kits, and `assets/`.**

## Fonts
Barlow, Manrope, and Libre Baskerville are loaded via Google Fonts `@import` in `tokens/fonts.css` (the source app also loads them from Google Fonts via `<link>`, not self-hosted files — so no substitution was needed and no font files exist to copy in).

## Index
- `styles.css` — root stylesheet, imports everything under `tokens/`
- `tokens/` — colors, typography, spacing, effects (shadow/blur/transition), fonts
- `components/core` — Button, GlassCard
- `components/feedback` — Badge, Chip
- `components/forms` — FormField
- `components/content` — EventCard
- `components/navigation` — NavBar
- `components/admin` — AdminButton, AdminStatusTag, AdminPanel, AdminTable, AdminFormField, AdminModal
- `guidelines/` — foundation specimen cards (Colors, Type, Spacing, Brand)
- `ui_kits/public-site/` — homepage + events click-through
- `ui_kits/admin-dashboard/` — dashboard + CRUD list click-through
- `thumbnail.html` — project tile
- `SKILL.md` — portable skill file for Claude Code

## Caveats — please help me iterate
- **No logo/brand-mark asset was available.** Attach `CPC_LOGO_24.png` (or a vector source) and I'll wire it into the nav, favicon, and UI kits.
- Admin has **two** visual layers in the real app — the older Bootstrap-shaped Flask-Admin CRUD screens (`admin.css`) and a newer Tailwind+MD3 dashboard shell (`dashboard.html`/`master.html`, not fully mirrored in `admin.css`). I modeled `AdminPanel`/`AdminTable`/`AdminStatusTag` off the CRUD layer since that's what `admin.css` defines in depth, and approximated the MD3 dashboard cards directly in the `admin-dashboard` UI kit without promoting them to reusable components yet — say the word if you want dedicated `StatCard`/`WizardCard` components.
- I have not yet built dedicated components/screens for Sermons, Podcasts, Teaching Series, Gallery, or Live Stream — those templates exist in the repo (`templates/sermons.html`, `podcasts.html`, `teaching-series.html`, `gallery.html`, `live.html`) and are good next candidates.
- Mobile nav (hamburger sheet), dropdown menus, and the footer ticker marquee are documented in the readme but not yet built as standalone components.
