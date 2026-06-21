#!/usr/bin/env python3
"""
Script to add show_in_banner column to announcements table.
Run from project root: python migrate_add_show_in_banner.py
"""
import os
import sqlite3

def add_column():
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'cpc_newhaven.db')
    if not os.path.exists(db_path):
        print("⚠️ Database not found at", db_path, "- create it by running the app first.")
        return
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(announcements)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'show_in_banner' in columns:
            print("✅ Column 'show_in_banner' already exists!")
        else:
            print("📝 Adding 'show_in_banner' column...")
            cursor.execute("""
                ALTER TABLE announcements
                ADD COLUMN show_in_banner BOOLEAN DEFAULT 0
            """)
            conn.commit()
            print("✅ Column 'show_in_banner' added successfully!")
        conn.close()
    except Exception as e:
        print("❌ Error:", e)

if __name__ == '__main__':
    add_column()
