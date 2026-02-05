#!/usr/bin/env python3
"""Add sort_order column to ongoing_events table."""
import os
import sqlite3

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'cpc_newhaven.db')
    if not os.path.exists(db_path):
        print("Database not found at", db_path)
        return
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(ongoing_events)")
        cols = [r[1] for r in cur.fetchall()]
        if 'sort_order' in cols:
            print("sort_order already exists")
        else:
            cur.execute("ALTER TABLE ongoing_events ADD COLUMN sort_order INTEGER DEFAULT 0")
            conn.commit()
            # Initialize existing rows with row number
            cur.execute("SELECT id FROM ongoing_events ORDER BY date_entered DESC")
            ids = [r[0] for r in cur.fetchall()]
            for i, id in enumerate(ids):
                cur.execute("UPDATE ongoing_events SET sort_order = ? WHERE id = ?", (i, id))
            conn.commit()
            print("Added sort_order and initialized order for", len(ids), "events")
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    migrate()
