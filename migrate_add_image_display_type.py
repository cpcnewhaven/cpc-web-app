#!/usr/bin/env python3
"""
Script to add image_display_type and show_in_banner columns to announcements table.
Uses the same database as the app (from DATABASE_URL or default).
Run from project root: python migrate_add_image_display_type.py
"""

import os
import sqlite3


def get_db_path():
    """Get SQLite path from app config (same as app.py)."""
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('DATABASE_URL', 'sqlite:///cpc_newhaven.db')
    if url.startswith('sqlite:///'):
        path = url.replace('sqlite:///', '')
        if os.path.exists(path):
            return path
        # Common case: db in instance/ when app uses default
        alt = os.path.join(os.path.dirname(__file__), 'instance', 'cpc_newhaven.db')
        if os.path.exists(alt):
            return alt
        return path  # use configured path so migration can create/use it
    return None


def add_columns():
    db_path = get_db_path()
    if not db_path:
        print("❌ Only SQLite is supported by this script. Set DATABASE_URL to a sqlite:/// path.")
        return
    if not os.path.exists(db_path):
        print("⚠️ Database not found at", os.path.abspath(db_path), "- run the app once to create it.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(announcements)")
        columns = [row[1] for row in cursor.fetchall()]

        for col_name, col_sql in [
            ('show_in_banner', 'ADD COLUMN show_in_banner BOOLEAN DEFAULT 0'),
            ('image_display_type', 'ADD COLUMN image_display_type VARCHAR(50)'),
        ]:
            if col_name in columns:
                print("✅ Column '%s' already exists!" % col_name)
            else:
                print("📝 Adding '%s' column..." % col_name)
                cursor.execute("ALTER TABLE announcements " + col_sql)
                conn.commit()
                print("✅ Column '%s' added successfully!" % col_name)

        conn.close()
    except Exception as e:
        print("❌ Error:", e)


if __name__ == '__main__':
    add_columns()

