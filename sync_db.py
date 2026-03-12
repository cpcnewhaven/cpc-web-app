#!/usr/bin/env python3
"""
Sync local database with live (production) database.

Pulls all content from LIVE_DATABASE_URL into your local database so you
develop against the same data as production. Run this whenever you want
to refresh local to match live.

Usage:
  # Required: set your production DB URL (e.g. from Render dashboard)
  export LIVE_DATABASE_URL="postgresql://user:pass@host/dbname"

  # Optional: set local DB (default: sqlite:///cpc_newhaven.db)
  export LOCAL_DATABASE_URL="sqlite:///cpc_newhaven.db"

  python sync_db.py              # pull live → local
  python sync_db.py --dry-run    # show what would be copied, no writes
  python sync_db.py --export     # export live to JSON file only (no local write)
"""

import os
import sys
import json
import argparse
from datetime import datetime, date
from urllib.parse import urlparse

# Ensure we load .env before app imports (app uses DATABASE_URL for "current" DB)
from dotenv import load_dotenv
load_dotenv()

# Use LOCAL as the app's database so Flask-SQLAlchemy writes to local
SOURCE_URL = os.getenv('LIVE_DATABASE_URL') or os.getenv('SOURCE_DATABASE_URL')
TARGET_URL = os.getenv('LOCAL_DATABASE_URL') or os.getenv('TARGET_DATABASE_URL') or 'sqlite:///cpc_newhaven.db'

if not SOURCE_URL:
    print("Error: LIVE_DATABASE_URL (or SOURCE_DATABASE_URL) must be set.", file=sys.stderr)
    print("Get the internal database URL from your Render dashboard (or production host).", file=sys.stderr)
    sys.exit(1)

# Live DB must have the same schema as the app (migrations applied on production).

if SOURCE_URL.startswith('postgres://'):
    SOURCE_URL = SOURCE_URL.replace('postgres://', 'postgresql://', 1)

# Point the app at LOCAL so that when we use db.session we write to local
os.environ['DATABASE_URL'] = TARGET_URL

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import app and models after setting DATABASE_URL so app uses local DB
from app import app
from database import db
from models import (
    GlobalIDCounter,
    BibleBook,
    BibleChapter,
    SermonSeries,
    User,
    Announcement,
    Sermon,
    PodcastSeries,
    PodcastEpisode,
    GalleryImage,
    OngoingEvent,
    TeachingSeries,
    TeachingSeriesSession,
    Paper,
    AuditLog,
    SiteContent,
)


def _serialize_value(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, (dict, list)):
        return val  # JSON columns
    return val


def _deserialize_value(val, col):
    if val is None:
        return None
    col_type = getattr(col, 'type', None)
    type_name = type(col_type).__name__ if col_type else ''
    if isinstance(val, str):
        if 'DateTime' in type_name or 'DATETIME' in str(col_type or ''):
            return datetime.fromisoformat(val.replace('Z', '+00:00'))
        if 'Date' in type_name and 'DateTime' not in type_name:
            return datetime.fromisoformat(val.replace('Z', '+00:00')).date()
    return val


# Order: parents before children (for insert). Children before parents (for delete).
# Tables with FKs: BibleChapter→BibleBook; PodcastEpisode→PodcastSeries;
# Sermon→User,SermonSeries,BibleBook,PodcastEpisode; TeachingSeriesSession→TeachingSeries
INSERT_ORDER = [
    GlobalIDCounter,
    BibleBook,
    User,
    SermonSeries,
    PodcastSeries,
    TeachingSeries,
    Announcement,
    OngoingEvent,
    GalleryImage,
    Paper,
    SiteContent,
    BibleChapter,
    PodcastEpisode,
    Sermon,
    TeachingSeriesSession,
    AuditLog,
]
DELETE_ORDER = list(reversed(INSERT_ORDER))


def row_to_dict(model, row):
    """Serialize one model instance to a dict (column values only)."""
    d = {}
    for col in model.__table__.columns:
        key = col.key
        val = getattr(row, key, None)
        d[key] = _serialize_value(val)
    return d


def dict_to_row(model, d):
    """Deserialize a dict into a new model instance (column values only)."""
    kwargs = {}
    for col in model.__table__.columns:
        key = col.key
        if key not in d:
            continue
        raw = d[key]
        kwargs[key] = _deserialize_value(raw, col)
    return model(**kwargs)


def pull_from_source(session_src):
    """Read all rows from source session into a dict of model_name -> list of dicts."""
    data = {}
    for model in INSERT_ORDER:
        name = model.__name__
        rows = session_src.query(model).all()
        data[name] = [row_to_dict(model, r) for r in rows]
        print(f"  {name}: {len(rows)} rows")
    return data


def apply_to_target(data, dry_run=False):
    """Replace local tables with data from the pulled snapshot."""
    with app.app_context():
        for model in DELETE_ORDER:
            name = model.__name__
            count = data.get(name, [])
            if dry_run:
                print(f"  [dry-run] would replace {name}: {len(count)} rows")
                continue
            # Delete existing rows (child tables first is already reflected in DELETE_ORDER)
            deleted = db.session.query(model).delete()
            if deleted:
                print(f"  {name}: deleted {deleted} local rows")
            for d in count:
                try:
                    obj = dict_to_row(model, d)
                    db.session.add(obj)
                except Exception as e:
                    print(f"  {name}: skip row {d.get('id', d)}: {e}", file=sys.stderr)
            if count:
                print(f"  {name}: inserted {len(count)} rows")
        if not dry_run:
            db.session.commit()
            print("Committed to local database.")


def main():
    parser = argparse.ArgumentParser(description="Sync local DB with live (pull from production).")
    parser.add_argument("--dry-run", action="store_true", help="Only show row counts, do not write to local.")
    parser.add_argument("--export", type=str, metavar="FILE", help="Export live data to JSON file only (no local write).")
    args = parser.parse_args()

    # Engine for source (live) — minimal options for read-only
    source_engine = create_engine(
        SOURCE_URL,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
    )
    SessionSrc = sessionmaker(bind=source_engine, autocommit=False, autoflush=False)

    print("Source (live):", urlparse(SOURCE_URL).hostname or "sqlite")
    print("Target (local):", urlparse(TARGET_URL).path if TARGET_URL.startswith("sqlite") else urlparse(TARGET_URL).hostname)
    print("Pulling from live...")

    try:
        session_src = SessionSrc()
        try:
            data = pull_from_source(session_src)
        finally:
            session_src.close()
    except Exception as e:
        print(f"Error connecting to live database: {e}", file=sys.stderr)
        sys.exit(1)

    if args.export:
        out_path = args.export
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Exported to {out_path}")
        return

    print("Applying to local...")
    apply_to_target(data, dry_run=args.dry_run)
    if args.dry_run:
        print("Dry run done. Run without --dry-run to apply.")


if __name__ == "__main__":
    main()
