#!/usr/bin/env python3
"""Export only public announcement fields from a database to JSON."""

import argparse
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()
FIELDS = (
    "id", "title", "description", "date_entered", "active", "type",
    "category", "tag", "superfeatured", "show_in_banner",
    "banner_sort_order", "archived", "featured_image",
    "image_display_type", "speaker", "expires_at", "event_date",
    "event_start_time", "event_end_time", "revision", "updated_at",
)


def json_value(value):
    return value.isoformat() if isinstance(value, (date, datetime)) else value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/announcements_snapshot.json")
    args = parser.parse_args()
    database_url = os.getenv("DATABASE_URL") or os.getenv("LIVE_DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL or LIVE_DATABASE_URL is required")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(database_url, pool_pre_ping=True)
    query = text("SELECT " + ", ".join(FIELDS) + " FROM announcements ORDER BY date_entered DESC")
    with engine.connect() as connection:
        rows = [
            {key: json_value(value) for key, value in dict(row._mapping).items()}
            for row in connection.execute(query)
        ]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "announcements table (public fields only)",
        "announcements": rows,
    }
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Exported {len(rows)} public announcements to {output}")


if __name__ == "__main__":
    main()
