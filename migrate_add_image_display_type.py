#!/usr/bin/env python3
"""
Script to add image_display_type column to announcements table
"""

from app import app
from database import db
import sqlite3

def add_column():
    """Add image_display_type column if it doesn't exist"""
    
    with app.app_context():
        db_path = 'instance/cpc_newhaven.db'
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if column exists
            cursor.execute("PRAGMA table_info(announcements)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'image_display_type' in columns:
                print("✅ Column 'image_display_type' already exists!")
            else:
                print("📝 Adding 'image_display_type' column...")
                cursor.execute("""
                    ALTER TABLE announcements 
                    ADD COLUMN image_display_type VARCHAR(50)
                """)
                conn.commit()
                print("✅ Column 'image_display_type' added successfully!")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    add_column()

