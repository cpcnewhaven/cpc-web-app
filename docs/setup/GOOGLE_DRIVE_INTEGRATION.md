# Google Drive Gallery Integration

This integration allows you to automatically sync photos from Google Drive directly into your CPC gallery, making content management much easier.

## 🚀 Quick Start

### Option 1: Automated Installation
```bash
./install_google_drive.sh
```

### Option 2: Manual Installation
```bash
pip install google-api-python-client google-auth-oauthlib google-auth
```

## 🔧 Setup Instructions

### 1. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click on it and press "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Choose "Desktop application" as the application type
   - Give it a name (e.g., "CPC Gallery Integration")
   - Click "Create"
5. Download the credentials:
   - Click the download button next to your new credentials
   - Save the file as `credentials.json` in your project root

### 2. Test the Integration

```bash
python setup_google_drive.py
```

### 3. Access the Admin Interface

1. Start your Flask application: `python app.py`
2. Go to `/admin/google-drive`
3. Follow the setup instructions in the interface

## 📁 Folder Organization

Organize your Google Drive photos in folders with descriptive names:

- **Events** - Church events and celebrations
- **Worship** - Sunday services and worship
- **Fellowship** - Community gatherings
- **Youth** - Youth group activities
- **Missions** - Mission trips and outreach

## 🏷️ Automatic Tagging

The system automatically creates tags based on:

- **Folder names**: "Events" → `["event"]`, "Worship" → `["worship"]`
- **File names**: "sunday-service-2024.jpg" → `["sunday", "service", "2024"]`
- **Event detection**: Files in event folders are marked as events

## 🔄 Sync Options

### Manual Sync
```bash
python google_drive_integration.py sync "CPC Gallery"
```

### Admin Interface
- Go to `/admin/google-drive`
- Enter folder name
- Click "Sync Now"

### Automatic Sync
- Configure sync intervals (daily, weekly, monthly)
- Enable automatic syncing in the admin interface

## 📊 Features

### Admin Dashboard
- Real-time sync status
- Folder browser
- Connection testing
- Sync configuration
- Help and troubleshooting

### Smart Features
- Automatic image detection
- Thumbnail generation
- Metadata extraction
- Duplicate prevention
- Error handling and logging

### Integration
- Works with existing gallery system
- Preserves manual entries
- Updates existing Google Drive entries
- Maintains gallery JSON structure

## 🛠️ API Endpoints

- `GET /admin/google-drive/` - Dashboard
- `POST /admin/google-drive/sync` - Sync gallery
- `GET /admin/google-drive/status` - Get sync status
- `GET /admin/google-drive/folders` - List folders
- `GET /admin/google-drive/test-connection` - Test connection

## 🔧 Configuration

### Sync Configuration
```json
{
  "folder_name": "CPC Gallery",
  "sync_interval": "daily",
  "enabled": true,
  "last_sync": "2024-01-15T10:30:00Z"
}
```

### Environment Variables
```bash
# Optional: Set custom paths
GOOGLE_DRIVE_CREDENTIALS_FILE=credentials.json
GOOGLE_DRIVE_TOKEN_FILE=token.pickle
GOOGLE_DRIVE_GALLERY_FILE=data/gallery.json
```

## 🐛 Troubleshooting

### Common Issues

1. **"Google APIs not available"**
   - Run: `pip install google-api-python-client google-auth-oauthlib google-auth`
   - Restart the application

2. **"Authentication failed"**
   - Check that `credentials.json` exists in project root
   - Verify Google Cloud Console setup
   - Delete `token.pickle` and re-authenticate

3. **"Folder not found"**
   - Check folder name spelling
   - Use the folder browser in admin interface
   - Ensure folder exists in Google Drive

4. **"No images found"**
   - Check folder contains image files
   - Verify folder permissions
   - Check file formats (JPG, PNG, GIF, WebP supported)

### Debug Mode
```bash
# Enable debug logging
export GOOGLE_DRIVE_DEBUG=1
python app.py
```

### Reset Integration
```bash
# Remove authentication token
rm token.pickle

# Remove Google Drive images from gallery
python -c "
import json
with open('data/gallery.json', 'r') as f:
    data = json.load(f)
filtered = [img for img in data if img.get('source') != 'google_drive']
with open('data/gallery.json', 'w') as f:
    json.dump(filtered, f, indent=2)
print('Google Drive images removed from gallery')
"
```

## 📝 File Structure

```
cpc-web-app/
├── google_drive_integration.py    # Main integration class
├── google_drive_routes.py         # Flask routes
├── setup_google_drive.py          # Setup script
├── install_google_drive.sh        # Installation script
├── requirements_google_drive.txt  # Dependencies
├── credentials.json               # Google API credentials (you create this)
├── token.pickle                   # Authentication token (auto-generated)
└── templates/admin/
    └── google_drive_dashboard.html # Admin interface
```

## 🔒 Security Notes

- `credentials.json` contains sensitive information - never commit to version control
- `token.pickle` contains authentication tokens - keep secure
- The integration only has read access to your Google Drive
- All API calls are made over HTTPS

## 📈 Performance

- Images are synced with thumbnails for faster loading
- Only new/changed images are processed on subsequent syncs
- Large folders are processed in batches
- Sync progress is tracked and can be resumed

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the admin dashboard for error messages
3. Check the application logs
4. Verify Google Cloud Console setup

## 🔄 Updates

The integration automatically handles:
- New images added to Google Drive
- Updated images (re-syncs with new metadata)
- Deleted images (removes from gallery)
- Folder structure changes

## 📱 Mobile Support

The admin interface is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones
- All modern browsers

---

**Happy syncing! 🎉**

Your Google Drive photos will now automatically appear in your CPC gallery with proper tagging and organization.
