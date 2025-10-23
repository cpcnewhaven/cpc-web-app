#!/usr/bin/env python3
"""
Google Drive Integration Setup Script
Helps set up Google Drive API credentials and test the integration
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    required_packages = [
        'google-api-python-client',
        'google-auth-oauthlib',
        'google-auth'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nInstalling missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✓ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install dependencies: {e}")
            return False
    
    return True

def create_credentials_template():
    """Create a template for credentials.json"""
    template = {
        "installed": {
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    credentials_file = Path('credentials_template.json')
    with open(credentials_file, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"✓ Created credentials template: {credentials_file}")
    return credentials_file

def setup_google_cloud_instructions():
    """Print instructions for setting up Google Cloud Console"""
    print("\n" + "="*60)
    print("GOOGLE CLOUD CONSOLE SETUP INSTRUCTIONS")
    print("="*60)
    print()
    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Create a new project or select an existing one")
    print("3. Enable the Google Drive API:")
    print("   - Go to 'APIs & Services' > 'Library'")
    print("   - Search for 'Google Drive API'")
    print("   - Click on it and press 'Enable'")
    print()
    print("4. Create OAuth 2.0 credentials:")
    print("   - Go to 'APIs & Services' > 'Credentials'")
    print("   - Click 'Create Credentials' > 'OAuth 2.0 Client ID'")
    print("   - Choose 'Desktop application' as the application type")
    print("   - Give it a name (e.g., 'CPC Gallery Integration')")
    print("   - Click 'Create'")
    print()
    print("5. Download the credentials:")
    print("   - Click the download button next to your new credentials")
    print("   - Save the file as 'credentials.json' in your project root")
    print()
    print("6. Run this script again to test the integration")
    print()

def test_integration():
    """Test the Google Drive integration"""
    print("Testing Google Drive integration...")
    
    try:
        from google_drive_integration import GoogleDriveGalleryManager
        
        manager = GoogleDriveGalleryManager()
        
        # Test authentication
        if manager.sync_service.authenticate():
            print("✓ Authentication successful")
            
            # Test folder listing
            try:
                results = manager.sync_service.service.files().list(
                    q="mimeType='application/vnd.google-apps.folder'",
                    fields="files(id, name)",
                    pageSize=5
                ).execute()
                
                folders = results.get('files', [])
                print(f"✓ Found {len(folders)} folders in Google Drive")
                
                if folders:
                    print("Sample folders:")
                    for folder in folders[:3]:
                        print(f"  - {folder['name']}")
                
            except Exception as e:
                print(f"✗ Error listing folders: {e}")
                return False
            
            return True
        else:
            print("✗ Authentication failed")
            return False
            
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("CPC Google Drive Integration Setup")
    print("="*40)
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found")
        print()
        setup_google_cloud_instructions()
        create_credentials_template()
        print("\nAfter setting up credentials.json, run this script again.")
        return
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Failed to install dependencies")
        return
    
    # Test integration
    if test_integration():
        print("\n✅ Google Drive integration is ready!")
        print("\nNext steps:")
        print("1. Run: python google_drive_integration.py sync")
        print("2. Or use the admin interface at /admin/google-drive")
    else:
        print("\n❌ Google Drive integration setup failed")
        print("Please check your credentials.json file and try again.")

if __name__ == "__main__":
    main()
