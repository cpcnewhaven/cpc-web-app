import sqlite3
import os

db_path = os.path.join('instance', 'cpc_newhaven.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if 'source' column exists
    cursor.execute("PRAGMA table_info(podcast_episodes)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'source' not in columns:
        print("Adding 'source' column...")
        cursor.execute("ALTER TABLE podcast_episodes ADD COLUMN source VARCHAR(50) DEFAULT 'manual'")
        
    if 'original_id' not in columns:
        print("Adding 'original_id' column...")
        cursor.execute("ALTER TABLE podcast_episodes ADD COLUMN original_id VARCHAR(200)")
        
    conn.commit()
    conn.close()
    print("Migration complete.")
else:
    print(f"Database not found at {db_path}")
