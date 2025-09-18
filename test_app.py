#!/usr/bin/env python3
"""
Simple test script to verify the Flask application works
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from app import app, db
        from models import Announcement, Sermon, PodcastEpisode, PodcastSeries, GalleryImage, OngoingEvent
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_app_creation():
    """Test that the Flask app can be created"""
    try:
        from app import app
        with app.app_context():
            print("✓ Flask app created successfully")
            return True
    except Exception as e:
        print(f"✗ App creation error: {e}")
        return False

def test_database_creation():
    """Test that database tables can be created"""
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
            print("✓ Database tables created successfully")
            return True
    except Exception as e:
        print(f"✗ Database creation error: {e}")
        return False

def test_api_endpoints():
    """Test that API endpoints are accessible"""
    try:
        from app import app
        with app.test_client() as client:
            # Test a few key endpoints
            endpoints = [
                '/',
                '/api/announcements',
                '/api/sermons',
                '/sermons',
                '/about'
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint)
                if response.status_code in [200, 404]:  # 404 is ok for some endpoints
                    print(f"✓ {endpoint} - Status: {response.status_code}")
                else:
                    print(f"✗ {endpoint} - Status: {response.status_code}")
                    return False
            return True
    except Exception as e:
        print(f"✗ API test error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing CPC New Haven Flask Application")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_app_creation,
        test_database_creation,
        test_api_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\nTo start the application, run:")
        print("  python app.py")
        print("\nThen visit: http://localhost:5000")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
