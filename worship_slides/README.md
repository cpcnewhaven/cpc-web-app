# Worship slides workspace

This feature is isolated under `worship_slides/` and mounted at `/slides`. It uses the app's existing staff login, while its OAuth flows and saved credentials are separate from the existing Planning Center calendar and gallery integrations.

## Connections

### Planning Center
Needs the app's OAuth client ID and secret, the `services` scope enabled, and this registered redirect URI:

`https://app.cpcnewhaven.org/slides/connect/planning-center/callback`

### Google Workspace
Needs an OAuth web client with the Google Drive API, Google Docs API, and Google Slides API enabled. Set `SLIDES_GOOGLE_CLIENT_ID` and `SLIDES_GOOGLE_CLIENT_SECRET`, then register:

`https://app.cpcnewhaven.org/slides/connect/google/callback`

Scopes:
- `https://www.googleapis.com/auth/drive`
- `https://www.googleapis.com/auth/documents`
- `https://www.googleapis.com/auth/presentations`

Tokens and settings are stored in the app database in separate `SiteContent` records (`worship_slides_google_tokens`, `worship_slides_pco_tokens`, `worship_slides_template_id`, `worship_slides_last_bulletin_id`).

## Worship preparation workflows

1. **Bulletin Google Doc to Standardized Slides (Primary flow)**:
   - Staff provide a Google Doc bulletin URL or ID (defaults to CPC's bulletin doc `1nDWJbDmvbf1PNYbHk9JMrjdihIrW2Cy9_MZoZBD-gNc`).
   - The engine parses the Order of Worship into liturgical categories (`liturgy`, `song`, `scripture`, `sermon`, `prayer`, `communion`, `announcement`).
   - Long readings and song verses are automatically chunked into readable slide blocks (3–5 lines per slide with verse labels).
   - Staff review and edit each item in the workspace editor.
   - Staff click **Populate Google Slides**: the workspace copies the standardized CPC template (`15zT3vmtW0ZYXYgm57qIkOAaLcNODjuNYQeur48w_oNw` by default or custom URL), duplicates its slide layouts, populates titles/lyrics/liturgy, and returns a direct link to the new slide deck.

2. **Planning Center Services plan**:
   - Staff browse service types and plans directly from Planning Center Services API.
   - Song lyrics are pulled from selected musical arrangements.

3. **Combined Bulletin + Planning Center piping**:
   - Staff import the Sunday bulletin Google Doc and choose the corresponding Planning Center plan.
   - Song lyrics, musical arrangements, and order details from Planning Center are piped directly into the matching bulletin song items.
