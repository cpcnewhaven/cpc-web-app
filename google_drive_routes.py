"""
Google Drive Routes for CPC Gallery
Flask routes for Google Drive integration
"""

from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
import os
import json
from datetime import datetime

# Try to import Google Drive integration, but make it optional
try:
    from google_drive_integration import GoogleDriveGalleryManager
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    GoogleDriveGalleryManager = None

# Create blueprint
google_drive_bp = Blueprint('google_drive', __name__, url_prefix='/admin/google-drive')

def check_google_drive_available():
    """Check if Google Drive integration is available"""
    if not GOOGLE_DRIVE_AVAILABLE:
        return jsonify({'error': 'Google Drive integration not available. Please install dependencies first.'})
    return None

@google_drive_bp.route('/')
def dashboard():
    """Google Drive integration dashboard"""
    if not GOOGLE_DRIVE_AVAILABLE:
        return render_template('admin/google_drive_dashboard.html', 
                             status={'error': 'Google Drive integration not available. Please install dependencies.'})
    
    manager = GoogleDriveGalleryManager()
    status = manager.get_sync_status()
    
    return render_template('admin/google_drive_dashboard.html', status=status)

@google_drive_bp.route('/setup')
def setup():
    """Setup Google Drive credentials"""
    if not GOOGLE_DRIVE_AVAILABLE:
        flash('Google Drive integration not available. Please install dependencies first.', 'error')
        return redirect(url_for('google_drive.dashboard'))
    
    manager = GoogleDriveGalleryManager()
    
    if manager.setup_credentials():
        flash('Please follow the instructions to set up Google Drive credentials', 'info')
    else:
        flash('Google Drive setup failed. Please check the console for instructions.', 'error')
    
    return redirect(url_for('google_drive.dashboard'))

@google_drive_bp.route('/sync', methods=['POST'])
def sync_gallery():
    """Sync gallery from Google Drive"""
    if not GOOGLE_DRIVE_AVAILABLE:
        flash('Google Drive integration not available. Please install dependencies first.', 'error')
        return redirect(url_for('google_drive.dashboard'))
    
    try:
        folder_name = request.form.get('folder_name', 'CPC Gallery')
        manager = GoogleDriveGalleryManager()
        
        if manager.sync_gallery(folder_name):
            flash(f'Successfully synced gallery from Google Drive folder: {folder_name}', 'success')
        else:
            flash('Failed to sync gallery from Google Drive', 'error')
    
    except Exception as e:
        flash(f'Error syncing gallery: {str(e)}', 'error')
    
    return redirect(url_for('google_drive.dashboard'))

@google_drive_bp.route('/status')
def get_status():
    """Get sync status as JSON"""
    manager = GoogleDriveGalleryManager()
    status = manager.get_sync_status()
    return jsonify(status)

@google_drive_bp.route('/test-connection')
def test_connection():
    """Test Google Drive connection"""
    try:
        manager = GoogleDriveGalleryManager()
        sync_service = manager.sync_service
        
        if sync_service.authenticate():
            return jsonify({
                'success': True,
                'message': 'Successfully connected to Google Drive'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to authenticate with Google Drive'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Connection test failed: {str(e)}'
        })

@google_drive_bp.route('/folders')
def list_folders():
    """List available Google Drive folders"""
    try:
        manager = GoogleDriveGalleryManager()
        sync_service = manager.sync_service
        
        if not sync_service.authenticate():
            return jsonify({'error': 'Authentication failed'})
        
        # Get all folders
        results = sync_service.service.files().list(
            q="mimeType='application/vnd.google-apps.folder'",
            fields="files(id, name, createdTime, modifiedTime)"
        ).execute()
        
        folders = results.get('files', [])
        
        return jsonify({
            'folders': folders,
            'count': len(folders)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@google_drive_bp.route('/preview/<folder_id>')
def preview_folder(folder_id):
    """Preview images in a specific folder"""
    try:
        manager = GoogleDriveGalleryManager()
        sync_service = manager.sync_service
        
        if not sync_service.authenticate():
            return jsonify({'error': 'Authentication failed'})
        
        # Get folder info
        folder_info = sync_service.service.files().get(fileId=folder_id).execute()
        
        # Get images in folder
        images = sync_service.list_images_in_folder(folder_id, max_results=20)
        
        return jsonify({
            'folder': folder_info,
            'images': images,
            'count': len(images)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@google_drive_bp.route('/sync-schedule', methods=['POST'])
def schedule_sync():
    """Schedule automatic sync"""
    try:
        data = request.get_json()
        folder_name = data.get('folder_name', 'CPC Gallery')
        sync_interval = data.get('sync_interval', 'daily')  # daily, weekly, monthly
        
        # Save sync configuration
        sync_config = {
            'folder_name': folder_name,
            'sync_interval': sync_interval,
            'last_sync': datetime.now().isoformat(),
            'enabled': True
        }
        
        with open('data/google_drive_sync_config.json', 'w') as f:
            json.dump(sync_config, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Sync schedule updated successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update sync schedule: {str(e)}'
        })

@google_drive_bp.route('/sync-config')
def get_sync_config():
    """Get current sync configuration"""
    try:
        config_file = 'data/google_drive_sync_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = {
                'folder_name': 'CPC Gallery',
                'sync_interval': 'daily',
                'enabled': False
            }
        
        return jsonify(config)
    
    except Exception as e:
        return jsonify({'error': str(e)})

@google_drive_bp.route('/manual-sync/<folder_id>')
def manual_sync_folder(folder_id):
    """Manually sync a specific folder"""
    try:
        manager = GoogleDriveGalleryManager()
        sync_service = manager.sync_service
        
        if not sync_service.authenticate():
            return jsonify({'error': 'Authentication failed'})
        
        # Get folder name
        folder_info = sync_service.service.files().get(fileId=folder_id).execute()
        folder_name = folder_info.get('name', 'Unknown Folder')
        
        # Sync the folder
        if manager.sync_gallery(folder_name):
            return jsonify({
                'success': True,
                'message': f'Successfully synced folder: {folder_name}'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to sync folder: {folder_name}'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error syncing folder: {str(e)}'
        })
