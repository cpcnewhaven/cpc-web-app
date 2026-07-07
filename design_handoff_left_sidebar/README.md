# Handoff: Left Dashboard Sidebar Redesign — Direction 1B

Recreate the **left dashboard sidebar** on the CPC New Haven site using **Direction 1B
(Content-first & minimal)**. This fixes the original problems: the sidebar duplicated the
top nav, had weak blue-on-blue hierarchy, too many peer sections, throwaway social icons,
and an unfinished search field.

## What's in this bundle
- **`1b_base.html_sidebar_partial.html`** — the new Jinja markup. Paste it INSIDE the
  existing `<aside class="dashboard-sidebar dashboard-left …">` block in
  `templates/base.html` (was ~lines 366–418), replacing that block's current contents.
  Keep the outer `<aside>` tag and its Alpine `x-show`/`$store.dash.showLeftSidebar` toggle.
- **`1b_style.css_additions.css`** — the CSS. Append to `static/css/style.css`. Includes
  `body.theme-white` overrides so the light theme keeps working.
- **`Sidebar Redesign.dc.html`** — the visual reference (open in a browser; shows 1A + 1B
  in full homepage context — build the **1B** one, on the right).

## Wire-up notes (do these, don't skip)
1. **Routes.** The `url_for(...)` endpoint names in the partial are placeholders
   (`search, live, sermons, podcasts, teaching_series, events, lifegroups, plan_a_visit,
   give`). Open the OLD sidebar block and map each to the real endpoint it linked to.
2. **Social URLs.** The three footer icons use `social_facebook / social_instagram /
   social_youtube` placeholders — swap for the church's real social links already in
   `base.html`.
3. **Search submit.** The form reuses your existing search route; confirm the query param
   name (`q`) matches your `search` view.
4. **Deps already present** — no new libraries. FontAwesome 6.5.1, Barlow, and Alpine.js
   are already loaded in `base.html`.
5. **Deliberately dropped** (they live in the top nav, so removing the duplication is the
   point): standalone Community, Resources, Contact, New Content, Pastor Teaching, and the
   old separate "Give/Contact/Plan a Visit/Resources" grid. Pastor Teaching folds into
   "Teaching Series"; Contact folds into "Plan a Visit".
6. **Mobile is untouched** — the sidebar is `hidden lg:block`; the bottom nav and "More"
   sheet stay as-is.

## Structure of 1B (top → bottom)
1. **Search** — borderless, single bottom rule, inset magnifier icon.
2. **Live hero card** — red gradient, pulsing dot, "Watch Live / 10:30a".
3. **Watch & Listen** — three clean list rows (Sermons, Podcasts, Teaching Series).
4. **This Week** — three icon-chip rows with subtitles (Events, LifeGroups, Plan a Visit).
5. **Give** — one solid white high-intent button.
6. **Follow along** — footer row: label + three larger social icon buttons.

## Suggested Claude Code prompt
> Drop this folder into the repo root, then in Claude Code:
>
> "Implement the left sidebar redesign in `design_handoff_left_sidebar/`. Replace the inner
> markup of the `.dashboard-left` aside in `templates/base.html` with
> `1b_base.html_sidebar_partial.html`, and append `1b_style.css_additions.css` to
> `static/css/style.css`. Map every `url_for()` placeholder and social URL to the real
> endpoints/links the old sidebar used, remove the old `.dashboard-section`/`.quick-links-grid`
> markup that's now unused for the left rail, and verify both `theme-blue` and `theme-white`
> render correctly. Don't touch the mobile nav or the right rail."

## Design tokens (reference)
- Section heading: `#c3daf7`, 800 / 11px / `letter-spacing:.16em` / uppercase (brighter than
  links → the contrast fix).
- Accent (icons, chips): `#9bc7ff` — maps to your existing `--surface-accent`.
- Live red: card `linear-gradient(150deg,#ec3f5d,#b0203f)`, dot `#fff` pulsing.
- Panel/glass, radii, and Barlow weights already match your codebase; the CSS reuses
  `var(--surface-accent, #9bc7ff)` where a token exists.
