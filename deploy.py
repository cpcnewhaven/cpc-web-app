#!/usr/bin/env python3
"""
Deployment script for CPC New Haven Flask application
"""
import os
import sys
from app import app, db

def init_database():
    """Initialize the database with tables"""
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully")

def migrate_data():
    """Run data migration if needed"""
    try:
        from migrate_data import main as migrate_main
        migrate_main()
        print("✓ Data migration completed successfully")
    except Exception as e:
        print(f"⚠ Data migration failed: {e}")

def main():
    """Main deployment function"""
    print("Starting CPC New Haven deployment...")
    
    # Initialize database
    init_database()
    
    # Run data migration
    migrate_data()
    
    print("✓ Deployment completed successfully!")
    print("Application is ready to serve requests.")

if __name__ == '__main__':
    main()
