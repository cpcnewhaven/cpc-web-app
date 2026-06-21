#!/usr/bin/env python3
"""
Script to add event_start_time and event_end_time columns to announcements table.
Run from project root: python migrate_add_announcement_times.py
"""
import os
import sqlite3

def add_columns():
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'cpc_newhaven.db')
    if not os.path.exists(db_path):
        print("⚠️ Database not found at", db_path, "- create it by running the app first.")
        return
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(announcements)")
        columns = [row[1] for row in cursor.fetchall()]
        
        changed = False
        if 'event_start_time' in columns:
            print("✅ Column 'event_start_time' already exists!")
        else:
            print("📝 Adding 'event_start_time' column...")
            cursor.execute("""
                ALTER TABLE announcements
                ADD COLUMN event_start_time VARCHAR(100)
            """)
            changed = True
            
        if 'event_end_time' in columns:
            print("✅ Column 'event_end_time' already exists!")
        else:
            print("📝 Adding 'event_end_time' column...")
            cursor.execute("""
                ALTER TABLE announcements
                ADD COLUMN event_end_time VARCHAR(100)
            """)
            changed = True
            
        if changed:
            conn.commit()
            print("✅ Columns added successfully!")
        else:
            print("ℹ️ No changes needed.")
            
        conn.close()
    except Exception as e:
        print("❌ Error:", e)

if __name__ == '__main__':
    add_columns()
