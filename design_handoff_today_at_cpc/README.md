# Handoff: Today at CPC — TV Dashboard

## Overview
A full-screen, 1920×1080 (16:9) television dashboard for the lobby/foyer at Christ Presbyterian Church. It shows today's worship service, this week's top three events, and a next-steps/QR strip. Designed for a TV running the page full-screen (browser kiosk mode), no scrolling, no interaction required from viewers.

## About the Design Files
`today-at-cpc.html` in this folder is a **design reference**, a static HTML/CSS prototype showing the intended look, layout, and copy. It is not production code to embed as-is. Recreate it in whatever environment will actually run on the TV (a plain static page served to a kiosk browser is likely fine as-is; if there's an existing app/CMS, rebuild the layout using its patterns and component library).

## Fidelity
**High-fidelity.** Colors, typography, spacing, and copy are final as shown. Treat pixel positions/sizes as authoritative.

## Layout
Root container: `1920×1080`, `48px` padary padding on all sides (safe area), flex column, `28px` gap between the header / main / bottom strip.

1. **Header** (96px tall, flex row, space-between)
   - Left: 72×72 circular logo mark (navy circle, gold 2px ring, simple cross icon) + wordmark "Christ Presbyterian Church" (Lora 26px/600) with "New Haven, Connecticut" eyebrow (Work Sans 15px, uppercase, letter-spacing 0.14em).
   - Center: "Today at CPC" (Lora 40px/600).
   - Right: live time (30px/600, tabular-nums) + date (16px) stacked, a 1px divider, then a weather pill (rounded 100px, navy bg) with sun icon, "69°F · New Haven" (18px/600) and "Clear skies" (13px).

2. **Main row** — CSS grid, columns `1.42fr 1fr`, gap 36px, fills remaining height.
   - **Left card ("Today")**: full-bleed photo background (`.cpc-photo` placeholder — drop the real Sunday worship photo here), rounded 22px corners, dark gradient overlay from bottom. Overlaid content, bottom-anchored with 44px side / 40px bottom inset:
     - Gold pill badge "Summer Schedule" top-left (36px inset).
     - "Worship — 10:30 AM" (Lora 64px/600).
     - "135 Whitney Avenue" with map-pin icon (22px).
     - "Teaching series: Luke" (20px, "Luke" bold cream).
     - One welcome sentence (20px, max-width 640px).
   - **Right column ("This Week")**: eyebrow label "This Week" (16px uppercase), then 3 equal-height event cards stacked with 18px gap, each:
     - 18px border radius, `oklch(0.255 0.045 262)` background, 1px border `oklch(0.36 0.04 262)`, 24px/28px padding.
     - Day/date block: 88px-wide rounded rect, day abbreviation (14px uppercase) over date number (32px/700 Lora).
     - Title (Lora 28px/600) + category pill (gold outline, 12px uppercase, e.g. Fellowship / Community / Volunteer).
     - Time + location line (17px, muted).
     - One-line description (17px).
     - Card 1: Thursday Picnics on the Lawn — Tue 22, 6:00 PM, CPC Front Lawn, Fellowship.
     - Card 2: Men's Bike Ride & Lunch — Sat 1, 9:00 AM, Canal Trail to Mikro, Community.
     - Card 3: BBQ Volunteers Needed — Wed 5, 4:45–7:00 PM, Trowbridge Square Park, Volunteer.

3. **Bottom strip** (158px tall, rounded 18px, same card background/border as event cards, flex row, 40px horizontal padding, 40px gap)
   - Left: "Next Steps" eyebrow + 3 pill buttons (rounded 100px, `oklch(0.3 0.05 262)` bg, gold icon, 20px/600 label): "New here? Plan your visit", "Join a LifeGroup", "View all events".
   - 1px vertical divider.
   - Right: 104×104 QR code placeholder (white rounded box, swap in a real QR image) + instruction text "Scan for this week's complete schedule" (19px, max-width 220px).

## Interactions & Behavior
- No click targets are required — TV-only, no cursor.
- Header clock/date update live every 30 seconds (see inline `<script>` in the prototype — `tick()` on load + `setInterval`).
- No other animation or state.

## Design Tokens
**Colors** (all defined in OKLCH; convert to hex if the target stack needs it):
- Background gradient: `oklch(0.21 0.04 262)` → `oklch(0.17 0.035 260)`
- Panel/card background: `oklch(0.24–0.26 0.045 262)`
- Card border: `oklch(0.36 0.04 262)`
- Cream text (primary): `oklch(0.96 0.01 90)`
- Cream text (secondary/body): `oklch(0.86 0.015 90)`
- Muted blue-gray (eyebrows, meta): `oklch(0.68–0.72 0.03 260)`
- Gold accent: `oklch(0.78 0.1 85)`

**Typography**
- Headline serif: Lora (500/600 weights, italic 500 available), Google Fonts.
- Body/UI sans: Work Sans (400/500/600/700), Google Fonts.
- Scale in use: 13, 14, 15, 16, 17, 18, 19, 20, 22, 26, 28, 30, 32, 40, 64px.

**Radii**: pills `100px`; cards `18px`; hero panel `22px`; QR box `14px`; date block `12px`.

**Spacing**: outer safe-area padding `48px`; section gaps `28–36px`; card padding `24px 28px`.

## Assets
- Logo: simple line-drawn cross icon (inline SVG in the prototype) — replace with the real CPC logo mark.
- Hero photo: placeholder only (`.cpc-photo` div) — needs a real Sunday worship/atmospheric photo.
- QR code: placeholder only (`.cpc-qr` div) — needs a real generated QR code linking to the events page.
- Icons: all other icons (map pin, weather sun, people, calendar) are simple inline SVGs, free to reuse or replace with an icon library already in the target codebase.

## Files
- `today-at-cpc.html` — the full static prototype (open directly in a browser at 1920×1080).
