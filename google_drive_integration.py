"""
Google Drive Integration for CPC Gallery
Handles authentication, file listing, and image synchronization
"""

import os
import json
import base64
import requests
from datetime import datetime, timedelta
import pickle
from typing import List, Dict, Optional
import logging

# Try to import Google API libraries, but make them optional
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    # Create dummy classes for when Google APIs are not available
    class Credentials:
        pass
    class InstalledAppFlow:
        pass
    class Request:
        pass
    class build:
        pass
    class HttpError(Exception):
        pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleDriveGallerySync:
    """Handles Google Drive integration for gallery management"""
    
    # Scopes for Google Drive API
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.creds = None
        
    def authenticate(self) -> bool:
        """Authenticate with Google Drive API"""
        if not GOOGLE_APIS_AVAILABLE:
            logger.error("Google APIs not available. Please install: pip install google-api-python-client google-auth-oauthlib")
            return False
            
        try:
            # Load existing credentials
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    self.creds = pickle.load(token)
            
            # If there are no valid credentials, get new ones
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Credentials file {self.credentials_file} not found")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            # Build the service
            self.service = build('drive', 'v3', credentials=self.creds)
            logger.info("Successfully authenticated with Google Drive")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
    def get_folder_id(self, folder_name: str) -> Optional[str]:
        """Get folder ID by name"""
        try:
            results = self.service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            if folders:
                return folders[0]['id']
            return None
            
        except HttpError as e:
            logger.error(f"Error getting folder ID: {str(e)}")
            return None
    
    def list_images_in_folder(self, folder_id: str, max_results: int = 100) -> List[Dict]:
        """List all images in a specific folder"""
        try:
            # Query for image files
            query = f"'{folder_id}' in parents and (mimeType contains 'image/')"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink, webContentLink, thumbnailLink)",
                orderBy="createdTime desc",
                pageSize=max_results
            ).execute()
            
            files = results.get('files', [])
            images = []
            
            for file in files:
                # Get file metadata
                file_metadata = self.service.files().get(
                    fileId=file['id'],
                    fields="id, name, mimeType, size, createdTime, modifiedTime, webViewLink, webContentLink, thumbnailLink, parents"
                ).execute()
                
                # Create image object
                image = {
                    'id': file['id'],
                    'name': file['name'],
                    'url': file.get('webContentLink', ''),
                    'thumbnail_url': file.get('thumbnailLink', ''),
                    'web_view_url': file.get('webViewLink', ''),
                    'mime_type': file['mimeType'],
                    'size': file.get('size', '0'),
                    'created': file.get('createdTime', ''),
                    'modified': file.get('modifiedTime', ''),
                    'folder_id': folder_id
                }
                
                # Extract tags from folder structure or filename
                image['tags'] = self._extract_tags(file['name'], folder_id)
                image['event'] = self._is_event_image(file['name'], folder_id)
                
                images.append(image)
            
            logger.info(f"Found {len(images)} images in folder {folder_id}")
            return images
            
        except HttpError as e:
            logger.error(f"Error listing images: {str(e)}")
            return []
    
    def _extract_tags(self, filename: str, folder_id: str) -> List[str]:
        """Extract tags from filename and folder structure"""
        tags = []
        
        # Extract from filename (remove extension and split by common delimiters)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Common delimiters
        delimiters = ['_', '-', ' ', '.']
        for delimiter in delimiters:
            if delimiter in name_without_ext:
                parts = name_without_ext.split(delimiter)
                tags.extend([part.lower() for part in parts if part])
                break
        
        # Add folder-based tags
        try:
            folder_info = self.service.files().get(fileId=folder_id).execute()
            folder_name = folder_info.get('name', '').lower()
            
            # Map folder names to tags
            folder_tag_map = {
                'events': ['event'],
                'worship': ['worship'],
                'fellowship': ['fellowship'],
                'youth': ['youth'],
                'missions': ['missions'],
                'sunday service': ['worship', 'sunday'],
                'bible study': ['bible study', 'education'],
                'community': ['community', 'fellowship']
            }
            
            for key, value in folder_tag_map.items():
                if key in folder_name:
                    tags.extend(value)
                    
        except Exception as e:
            logger.warning(f"Could not get folder info: {str(e)}")
        
        # Remove duplicates and empty strings
        tags = list(set([tag.strip() for tag in tags if tag.strip()]))
        return tags
    
    def _is_event_image(self, filename: str, folder_id: str) -> bool:
        """Determine if image is from an event"""
        event_keywords = ['event', 'celebration', 'party', 'gathering', 'meeting', 'conference']
        
        # Check filename
        filename_lower = filename.lower()
        if any(keyword in filename_lower for keyword in event_keywords):
            return True
        
        # Check folder name
        try:
            folder_info = self.service.files().get(fileId=folder_id).execute()
            folder_name = folder_info.get('name', '').lower()
            if any(keyword in folder_name for keyword in event_keywords):
                return True
        except Exception as e:
            logger.warning(f"Could not check folder name: {str(e)}")
        
        return False
    
    def sync_to_gallery_json(self, folder_name: str, output_file: str = 'data/gallery.json') -> bool:
        """Sync Google Drive images to gallery JSON file"""
        try:
            # Authenticate
            if not self.authenticate():
                return False
            
            # Get folder ID
            folder_id = self.get_folder_id(folder_name)
            if not folder_id:
                logger.error(f"Folder '{folder_name}' not found")
                return False
            
            # Get images
            images = self.list_images_in_folder(folder_id)
            if not images:
                logger.warning(f"No images found in folder '{folder_name}'")
                return False
            
            # Convert to gallery format
            gallery_images = []
            for img in images:
                gallery_img = {
                    'id': f"gd_{img['id']}",  # Prefix to distinguish from manual entries
                    'name': img['name'],
                    'url': img['url'],
                    'size': img['size'],
                    'type': img['mime_type'],
                    'created': img['created'][:10] if img['created'] else datetime.now().strftime('%Y-%m-%d'),
                    'tags': img['tags'],
                    'event': img['event'],
                    'source': 'google_drive',
                    'folder_id': img['folder_id'],
                    'web_view_url': img['web_view_url']
                }
                gallery_images.append(gallery_img)
            
            # Load existing gallery data
            existing_images = []
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r') as f:
                        existing_data = json.load(f)
                        # Keep non-Google Drive images
                        existing_images = [img for img in existing_data if not img.get('source') == 'google_drive']
                except Exception as e:
                    logger.warning(f"Could not load existing gallery data: {str(e)}")
            
            # Merge with existing data
            all_images = existing_images + gallery_images
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump(all_images, f, indent=2)
            
            logger.info(f"Successfully synced {len(gallery_images)} images to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            return False
    
    def get_image_thumbnail(self, file_id: str, size: str = 'medium') -> Optional[str]:
        """Get thumbnail URL for an image"""
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields="thumbnailLink"
            ).execute()
            
            thumbnail_url = file_metadata.get('thumbnailLink', '')
            if thumbnail_url:
                # Modify thumbnail size if needed
                if size == 'small':
                    thumbnail_url = thumbnail_url.replace('=s220', '=s100')
                elif size == 'large':
                    thumbnail_url = thumbnail_url.replace('=s220', '=s800')
            
            return thumbnail_url
            
        except Exception as e:
            logger.error(f"Error getting thumbnail: {str(e)}")
            return None

class GoogleDriveGalleryManager:
    """High-level manager for Google Drive gallery operations"""
    
    def __init__(self, credentials_file: str = 'credentials.json'):
        self.sync_service = GoogleDriveGallerySync(credentials_file)
        self.gallery_file = 'data/gallery.json'
    
    def setup_credentials(self) -> bool:
        """Guide user through setting up Google Drive credentials"""
        print("Setting up Google Drive integration...")
        print("\n1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Google Drive API")
        print("4. Create credentials (OAuth 2.0 Client ID)")
        print("5. Download credentials.json and place in project root")
        print("6. Run this script again to authenticate")
        
        if not os.path.exists('credentials.json'):
            print("\n❌ credentials.json not found. Please follow the steps above.")
            return False
        
        return True
    
    def sync_gallery(self, folder_name: str = "CPC Gallery") -> bool:
        """Sync Google Drive folder to gallery"""
        print(f"Syncing Google Drive folder: {folder_name}")
        
        if not os.path.exists('credentials.json'):
            print("❌ credentials.json not found. Run setup_credentials() first.")
            return False
        
        success = self.sync_service.sync_to_gallery_json(folder_name, self.gallery_file)
        
        if success:
            print(f"✅ Successfully synced gallery from Google Drive")
        else:
            print("❌ Failed to sync gallery")
        
        return success
    
    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        status = {
            'has_credentials': os.path.exists('credentials.json'),
            'has_token': os.path.exists('token.pickle'),
            'gallery_file_exists': os.path.exists(self.gallery_file),
            'last_sync': None
        }
        
        if status['gallery_file_exists']:
            try:
                with open(self.gallery_file, 'r') as f:
                    data = json.load(f)
                    google_drive_images = [img for img in data if img.get('source') == 'google_drive']
                    status['google_drive_images_count'] = len(google_drive_images)
                    status['total_images_count'] = len(data)
            except Exception as e:
                status['error'] = str(e)
        
        return status

# CLI interface
if __name__ == "__main__":
    import sys
    
    manager = GoogleDriveGalleryManager()
    
    if len(sys.argv) < 2:
        print("Usage: python google_drive_integration.py [command]")
        print("Commands:")
        print("  setup     - Setup Google Drive credentials")
        print("  sync      - Sync gallery from Google Drive")
        print("  status    - Check sync status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "setup":
        manager.setup_credentials()
    elif command == "sync":
        folder_name = sys.argv[2] if len(sys.argv) > 2 else "CPC Gallery"
        manager.sync_gallery(folder_name)
    elif command == "status":
        status = manager.get_sync_status()
        print("Sync Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    else:
        print(f"Unknown command: {command}")
