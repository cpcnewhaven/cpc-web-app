#!/usr/bin/env python3
"""Apply a reviewed weekly content batch; preview changes unless --apply is set."""
import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def apply_batch(payload, commit=False):
    from app import db, cache
    from models import Announcement, OngoingEvent, GlobalIDCounter, next_global_id

    # Serialize new ID allocation against other imports.
    GlobalIDCounter.query.with_for_update().all()
    changes = []
    fields = ('title', 'description', 'type', 'category', 'active', 'archived',
              'superfeatured', 'event_date', 'expires_at', 'event_start_time', 'event_end_time',
              'featured_image', 'image_display_type')
    for row in payload['announcements']:
        existing_id = row.get('existing_id')
        ann = db.session.get(Announcement, existing_id) if existing_id else None
        if existing_id and (not ann or ann.title != row['title']):
            # Do not overwrite a different site's record just because its ID matches.
            if ann:
                raise ValueError(f'Announcement {existing_id} no longer matches the reviewed title')
            ann = None
        if not ann:
            ann = Announcement.query.filter_by(title=row['title'], archived=False).first()
        values = {k: row.get(k) for k in fields}
        for key in ('event_date', 'expires_at'):
            values[key] = date.fromisoformat(values[key]) if values[key] else None
        if ann and all(getattr(ann, k) == v for k, v in values.items()):
            continue
        if not ann:
            ann = Announcement(id=next_global_id(), revision=0)
            db.session.add(ann)
        for key, value in values.items():
            setattr(ann, key, value)
        ann.date_entered = datetime.fromisoformat(row['date_entered'])
        ann.updated_at = datetime.utcnow()
        ann.updated_by = 'weekly-newsletter-2026-10-30'
        ann.revision = (ann.revision or 0) + 1
        changes.append(f'Update {ann.id}: {ann.title}')
    # The ongoing section has its own table; keep it aligned with the same copy.
    for row in payload['announcements']:
        if row['type'] != 'ongoing':
            continue
        event = OngoingEvent.query.filter_by(title=row['title']).first()
        values = {k: row[k] for k in ('title', 'description', 'type', 'category', 'active', 'archived')}
        values['expires_at'] = date.fromisoformat(row['expires_at']) if row['expires_at'] else None
        if event and all(getattr(event, k) == v for k, v in values.items()):
            continue
        if not event:
            event = OngoingEvent(id=next_global_id(), sort_order=0)
            db.session.add(event)
        for key, value in values.items():
            setattr(event, key, value)
        event.date_entered = datetime.fromisoformat(row['date_entered'])
        changes.append(f'Update ongoing {event.id}: {event.title}')
    for identifier in payload.get('archive_ids', []):
        ann = db.session.get(Announcement, identifier)
        # This batch only archives confirmed superseded entries.
        expected = {536: 'CPC Worship Night', 500: 'Adult Class | "The Wonders of Communal Worship"'}
        if ann and ann.title == expected.get(identifier) and (ann.active or not ann.archived):
            ann.active, ann.archived = False, True
            ann.revision = (ann.revision or 0) + 1
            changes.append(f'Archive {ann.id}: {ann.title}')
    if commit:
        db.session.commit()
        cache.clear()
    else:
        db.session.rollback()
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch', nargs='?', default=str(ROOT / 'data/newsletters/2026-10-30.json'))
    parser.add_argument('--apply', action='store_true', help='Commit the reviewed changes to DATABASE_URL')
    args = parser.parse_args()
    from app import app
    with app.app_context():
        changes = apply_batch(json.loads(Path(args.batch).read_text()), commit=args.apply)
        print('\n'.join(changes) or 'Already up to date.')
        print('Saved.' if args.apply else 'Preview only; rerun with --apply to save.')


if __name__ == '__main__':
    main()
