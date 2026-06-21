import sqlite3
import os
import sys

def migrate():
    db_path = 'instance/cpc_newhaven.db'
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Add full_name column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN full_name VARCHAR(100)")
            print("Added 'full_name' column to 'users' table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("'full_name' column already exists.")
            else:
                raise e

        # 2. Populate full_name with title-cased username as a starting point
        cursor.execute("SELECT id, username, full_name FROM users")
        users = cursor.fetchall()
        
        for user_id, username, full_name in users:
            if not full_name:
                # Basic title-casing (e.g. "john" -> "John")
                new_full_name = username.title()
                cursor.execute("UPDATE users SET full_name = ? WHERE id = ?", (new_full_name, user_id))
                print(f"Updated user '{username}' with default full_name '{new_full_name}'")

        conn.commit()
        conn.close()
        print("Migration completed successfully.")
        return True

    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate()
