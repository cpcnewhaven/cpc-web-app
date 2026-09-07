"""Read the public announcement snapshot without mutating a database."""

import json
import os
from datetime import date, datetime
from types import SimpleNamespace


SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), "data", "announcements_snapshot.json")


def _date(value):
    return date.fromisoformat(value[:10]) if value else None


def _datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None) if value else None


def load_snapshot(path=SNAPSHOT_PATH):
    """Return snapshot rows as template-compatible objects."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows = payload.get("announcements", []) if isinstance(payload, dict) else payload
        objects = []
        for row in rows:
            values = dict(row)
            values.update(
                date_entered=_datetime(row.get("date_entered")),
                updated_at=_datetime(row.get("updated_at")),
                expires_at=_date(row.get("expires_at")),
                event_date=_date(row.get("event_date")),
            )
            objects.append(SimpleNamespace(**values))
        return objects
    except (OSError, ValueError, TypeError):
        return []
