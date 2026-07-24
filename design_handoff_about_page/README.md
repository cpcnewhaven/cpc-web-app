# Handoff: About Page Redesign — Christ Presbyterian Church

## Overview
A redesign of the CPC New Haven public-site "About" page. Goal: keep the site's existing navy glassmorphic brand, but make the page feel warmer and less boxy/corporate — fewer nested bordered panels, full-bleed photography, warm pull-quote breaks, and simplified emphasis styling.

## About the Design Files
The files in this bundle are **design references built in HTML/React** (loaded via CDN + Babel in-browser) — they show intended look, content, and layout, not production code to copy directly. The task is to **recreate this design in the actual cpc-web-app Flask/Jinja templates**, using the existing `style.css` design tokens and component classes (`.btn`, `.glass-card`, etc.) already in the codebase, not by shipping this HTML as-is.

## Fidelity
**High-fidelity.** Colors, typography, spacing, and copy are final/near-final. Recreate pixel-for-real using the existing site's CSS variables and glass-card patterns — this bundle's inline styles map directly to those tokens (see Design Tokens below).

## Screens / Views
Single scrolling page, `About Page.html` (React tree in `About Page.jsx`), sections top to bottom:

1. **Fixed NavBar** — floating glass nav, centered, `max-width:1200px`, `top:20px`. Reuses the site's existing NavBar component; "About" marked active.

2. **Hero** — full-bleed photo (`78vh`, min-height 480px) with a bottom-weighted gradient overlay (`rgba(9,32,58,.35)→.55→solid #0a3d75`) so it blends into the page background instead of a hard-edged photo box. Headline "You are welcome here" (Manrope 800, 3.2rem, white, text-shadow), subhead paragraph, two CTAs: `Plan Your Visit` (primary) and `Watch Live` (glass).

3. **Pull-quote break** — cream/warm card (`linear-gradient(135deg,#fbf7ee,#f4ede0)`, border `#ece2cc`, radius 20px, shadow `0 12px 40px rgba(0,0,0,.18)`), serif italic quote, max-width 780px, centered. Used twice (welcome quote + Augustine quote in Total Christ section). This is the "warmth break" device — light surface against the dark page.

4. **Our Mission** — two-column (1fr/1fr) text + image. Mission paragraph with three emphasis words (**growing / acting / trusting**) styled as inline warm-gold (`#e3bd7d`) bold text, NOT boxed pills (this was the main "unwelcoming" fix from the original). CTA button "What We Believe →" (currently a placeholder link — no target page content was defined yet, ask the user before building it out).

5. **Our Total Christ Spirituality** — centered heading + intro paragraph + Augustine pull-quote (see #3).

6. **The Five Marks** — 5-card responsive grid (`auto-fit, minmax(230px,1fr)`), low-contrast cards (`rgba(255,255,255,.06)` bg, `1px solid rgba(255,255,255,.1)` border, radius 16px, no shadow) — intentionally lighter-weight than the old fully-bordered panel treatment. Cards: Gospel-Centered, Missional, Confessional, Sacramental, Communal — title + one condensed paragraph each (source copy trimmed for readability; full original copy is longer, ask the user if the fuller text is wanted).

7. **Leadership** — three groups (Our Staff Team, Session of Elders, Women's Leadership Board), each a responsive grid of circular photo + name + role, `minmax(110px,1fr)` columns, gap 24px, max-width 900px. Elder/WLB blurbs are condensed one-liners (original source copy included full BCO-language paragraphs — trim vs. restore is a content decision for the user). Full roster names/roles are in `About Page.jsx`.

8. **Life Together (photo gallery)** — asymmetric 3-column/2-row grid (not a uniform crop grid) for a more organic feel: one tall image spans both rows, two square-ish images, one wide image spans two columns. All images share `radius:20px`.

9. **Closing CTA** — "Come as you are" + welcome copy + `Plan Your Visit` (primary) / `Get in Touch` (secondary) buttons.

## Not yet included
The user's source content also contained an **Our Story** timeline (1991 founding → 2017 Mission Anabaino) and a **Servant Leadership Board** roster — these were not in scope for this pass. Ask the user if they want them added before treating this as final.

## Interactions & Behavior
- All CTAs are visual only in this prototype (no real navigation/links wired).
- Photo placeholders (`<image-slot>`) are drag-and-drop fillable in the Omelette editor only — in a real build, replace with real `<img>`/background-image and the real photography.
- No responsive/mobile breakpoints have been built yet — this is a desktop-width (1200px max content) reference only. Mobile behavior (nav collapse, single-column stacking of the two-column Mission section, grid reflow) needs to be designed before implementation.

## Design Tokens
Pulls directly from the CPC Design System bundle — see `_ds/cpc-design-system-f4f503d2-5000-45de-a97d-0d5baf4aa1c9/tokens/*.css` in this folder for the canonical values:
- **Colors**: `--bg-gradient` (navy diagonal), `--glass-white`, `--glass-border`, `--surface-text`, `--surface-muted`, `--cpc-blue` (#0052a3)
- **New in this design**: warm gold accent `#e3bd7d` for inline emphasis and kicker labels (not yet a token in the DS — recommend adding as `--accent-warm` if adopted sitewide), and the cream quote-card gradient `#fbf7ee → #f4ede0` (also not yet tokenized).
- **Type**: Manrope (`--font-display`) for headings, Barlow (`--font-primary`) for body, Libre Baskerville (`--font-serif`) for pull-quotes only.
- **Radius**: 16px (mark cards), 20px (photos, quote cards), full circle (avatars).
- **Shadow**: quote card `0 12px 40px rgba(0,0,0,.18)`.

## Assets
All photography is placeholder (`<image-slot>` drag-and-drop components) — the user said real photos will be attached after this handoff. Every slot has a descriptive `placeholder` string in `About Page.jsx` indicating what photo belongs there (e.g. "Congregation gathered in worship", "Fellowship at CPC").

## Files
- `About Page.html` — page shell, loads DS bundle + fonts/tokens + React/Babel CDN + `About Page.jsx`
- `About Page.jsx` — full page markup/content (single React component tree)
- `image-slot.js` — placeholder image component (dev reference only, not for production use)
- `_ds/` — the full CPC Design System bundle (tokens, compiled component bundle, stylesheet) this design was built against
