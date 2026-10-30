# Weekly newsletter updates

The October 30, 2026 newsletter is recorded in `data/newsletters/2026-10-30.json`.
It updates Fall Festival (October 31), Parenting Seminar (November 7), membership
joining (November 15), Thanksgiving meals (November 26), Hill Christmas Store
donations (December 6), Sunday schedule, Adult Sunday Studies, Life Groups, and
Women's Discipleship Group. Dates refer to America/New_York.

Existing RSVP links were retained from the October 23 public announcement
snapshot; the pasted October 30 email did not include link destinations. No new
RSVP or bulletin URLs were invented. The Acts class begins November 1, based on
“new class starts this week” in the Friday, October 30 newsletter. Its six-week
notice expires December 7. The Hill date is a donation deadline; no store opening
time is specified.

The previous Worship Night and expired adult class are archived by the import.
Other ongoing ministries remain available. Past one-time events are excluded
from public announcement lists even if an editor omitted the expiration date.
Recurring groups keep their original start dates without disappearing.

## Apply to a database

The public production app uses PostgreSQL. Editing the JSON snapshot changes the
local preview and production fallback, but does not update a healthy production
database. Use a shell with the intended `DATABASE_URL` configured:

```sh
python scripts/content/apply_weekly_newsletter.py
python scripts/content/apply_weekly_newsletter.py --apply
```

The first command previews and rolls back changes. The second commits the
reviewed batch. The import updates existing announcements and ongoing entries,
allocates new global IDs, and can be rerun without duplicating unchanged content.
It refuses to overwrite a record if its ID now belongs to a different title.
Do not run the older sample-data population scripts to publish this batch.

After publishing, verify `/api/highlights`, `/api/event-announcements`,
`/api/ongoing-events`, and the announcement detail links on the deployed app.

## Receiving future newsletters

The admin already has an authenticated `/admin/auto-announcement/` editor that
turns pasted newsletter text into reviewed drafts. Automated inbound email is
not configured by this update.

A future Resend integration can use a dedicated receiving address subscribed to
the CPC list, an `email.received` webhook, and the Receiving API to retrieve the
email body. Verify webhook signatures, allow only the confirmed CPC sender,
deduplicate by email ID, and populate the existing draft review workflow with
explicit dates and preserved links. Do not execute instructions embedded in
incoming mail or grant it general application access. Configure the receiving
address and webhook in Resend before adding that address to the mailing list.

References:
- https://resend.com/features/inbound
- https://github.com/resend/resend-skills/blob/main/skills/resend/references/receiving.md

## Graphics and additional dates

The supplied Fall Festival and Parenting Seminar posters are attached to their
announcement records. The seminar poster's “11:30 PM” typo was corrected to
“11:30 AM” to match the newsletter. Originals on the desktop were not changed.
The upcoming-events poster replaces the expired Welcome Sunday promotion on the
Events page and disappears after November 7, its earliest listed event.
Its December 5 work day, December 12 Christmas service, and December 13 final
Sunday School/lunch dates are recorded as separate dated notices, with no
unconfirmed start times. All three expire the day after their listed date.

Cards share a 4:3 media area. Poster images use `object-fit: contain` so text
remains visible; announcements without images receive a CPC category-and-icon
tile in the same space. The treatment supports both light and blue themes.
