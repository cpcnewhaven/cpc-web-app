# Possibly DELETE Folder

This folder contains files that may be outdated or no longer needed. Review before deleting.

## Files Moved Here

### Templates (Glass Versions - Not Used)
- `base_glass.html` - Alternative glass base template (not used, main app uses base.html)
- `index_glass.html` - Alternative glass homepage (not used)
- `sermons_glass.html` - Alternative glass sermons page (not used)
- `events_glass.html` - Alternative glass events page (not used)
- `admin_glass.html` - Alternative glass admin (replaced by Flask-Admin)
- `liquid_glass_demo.html` - Demo page (commented out route in app.py)
- Note: `test_podcasts.html` not found (may have been deleted already)

### Python Files (One-Time Scripts or Alternatives)
- `app_simple.py` - Simplified Flask app (alternative to app.py, may be used for deployment)
- `integrate_enhancements.py` - One-time integration script
- `fix_podcast_endpoints.py` - One-time fix script
- `test_app.py` - Test script
- `migrate_data.py` - Data migration script (one-time use)
- `deploy.py` - Deployment script (may be outdated)
- `sermon_enhancer.py` - Enhancement script (may be one-time)
- `database_sync.py` - Database sync script (may be outdated)

### Configuration Files (May Still Be Used)
- `README_SIMPLE.md` - Documentation for simplified app
- `requirements_simple.txt` - Requirements for app_simple.py
- `render_simple.yaml` - Render deployment config for app_simple.py
- Note: `Procfile` and `render.yaml` still reference app_simple.py - update these if you're using app.py

### Log Files
- `podcast_master.log` - Empty log file
- `podcast_scheduler.log` - Empty log file

## Important Notes

⚠️ **WARNING**: Some files here might still be referenced:
- `app_simple.py` is referenced in `Procfile` and `render.yaml`
- If you're using these for deployment, update them to use `app.py` instead

## Review Before Deleting

1. Check if any deployment configs reference files in this folder
2. Verify that main app (app.py) doesn't need any of these
3. Check git history if unsure about file purpose
4. Test deployment if you remove app_simple.py references

## Next Steps

1. Update `Procfile` to use `app.py` if not using `app_simple.py`
2. Update `render.yaml` to use `app.py` if not using `app_simple.py`
3. After confirming, you can safely delete files from this folder
4. Or restore specific files if needed

