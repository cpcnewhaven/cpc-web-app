#!/usr/bin/env python3
"""
Migration script to add 'source' and 'original_id' columns to podcast_episodes table.
Connects to Postgres via DATABASE_URL environment variable.
Safe to re-run: checks if columns already exist before adding them.
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate():
    """Add source and original_id columns to podcast_episodes table."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    try:
        import psycopg2
        from psycopg2 import sql
    except ImportError:
        logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
        sys.exit(1)

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Check if 'source' column exists
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='podcast_episodes' AND column_name='source'
        """)
        source_exists = cursor.fetchone() is not None

        # Check if 'original_id' column exists
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='podcast_episodes' AND column_name='original_id'
        """)
        original_id_exists = cursor.fetchone() is not None

        if not source_exists:
            logger.info("Adding 'source' column to podcast_episodes table...")
            cursor.execute("""
                ALTER TABLE podcast_episodes
                ADD COLUMN source VARCHAR(50) DEFAULT 'manual'
            """)
            logger.info("Added 'source' column successfully")
        else:
            logger.info("'source' column already exists")

        if not original_id_exists:
            logger.info("Adding 'original_id' column to podcast_episodes table...")
            cursor.execute("""
                ALTER TABLE podcast_episodes
                ADD COLUMN original_id VARCHAR(200)
            """)
            logger.info("Added 'original_id' column successfully")
        else:
            logger.info("'original_id' column already exists")

        conn.commit()
        cursor.close()
        conn.close()

        if not source_exists or not original_id_exists:
            logger.info("Migration completed successfully!")
        else:
            logger.info("No migration needed: columns already exist")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
