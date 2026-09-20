# Planning Center Calendar integration

The site can turn Planning Center Calendar events into local event announcements. A Planning Center event is identified in the announcement description with a marker such as `[planning-center-event:12345]`; later webhook deliveries update that same announcement instead of creating duplicates.

## Planning Center setup

1. In Planning Center Developer, create a Personal Access Token for a user who can read Calendar. Use the token's client ID and token as `PLANNING_CENTER_CLIENT_ID` and `PLANNING_CENTER_PERSONAL_ACCESS_TOKEN`.
2. Set `PLANNING_CENTER_CALENDAR_ID` if only one Calendar should be synchronized. Leave it empty to read organization events.
3. In the Planning Center webhook manager, create a subscription pointing to:

   `https://<your-site-host>/webhooks/planning-center`

   Subscribe to Calendar event create/update/delete notifications and copy the webhook authenticity secret into `PLANNING_CENTER_WEBHOOK_SECRET`.
4. Add all four environment variables to the deployment environment. Do not commit the token or webhook secret.
5. Run the admin sync once with an authenticated POST to `/admin/planning-center/sync` to backfill existing events. New changes will then arrive through the webhook.

The webhook endpoint verifies `X-PCO-Webhooks-Authenticity` with HMAC-SHA256. Planning Center retries failed deliveries, so the handler returns an error when it cannot safely process a valid event.

