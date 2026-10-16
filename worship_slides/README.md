# Worship slides workspace

This feature is isolated under `worship_slides/` and mounted at `/slides`. It uses the app's existing staff login, while its OAuth flows and saved credentials are separate from the existing Planning Center calendar and gallery integrations.

## Connections

Planning Center needs the app's OAuth client ID and secret, the `services` scope enabled, and this registered redirect URI:

`https://app.cpcnewhaven.org/slides/connect/planning-center/callback`

Google needs an OAuth web client with the Google Docs API and Google Slides API enabled. Set `SLIDES_GOOGLE_CLIENT_ID` and `SLIDES_GOOGLE_CLIENT_SECRET`, then register:

`https://app.cpcnewhaven.org/slides/connect/google/callback`

The Google connection asks for `drive.file` and `documents`, limiting Drive access to files created by this workspace and document creation/editing. Tokens are stored in the app database in separate `SiteContent` records.

## Current flow

Staff select a Planning Center Services type and plan, review/edit each imported item, then create a Google Slides deck, a Google Doc, or both. Song lyrics come from the plan item's selected arrangement. Projected lyrics/readings are split into short blocks of up to five non-empty lines. No existing CRUD models or endpoints are changed by this feature.
