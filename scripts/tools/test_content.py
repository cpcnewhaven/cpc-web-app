os.environ["FLASK_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite:///cpc_newhaven.db"
# Allow running from any directory by pointing Python at the project root
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app import app, ContentFeedView
import traceback

with app.test_request_context('/admin/content_feed/'):
    try:
        from flask_login import login_user
        from models import User
        # Mock authentication if needed, or bypass
        app.config['LOGIN_DISABLED'] = True
        
        view = ContentFeedView(name='All content', endpoint='content_feed', category='Content')
        res = view.index()
        print("SUCCESS! ContentFeedView ran.")
    except Exception as e:
        print("ERROR IN ContentFeedView:")
        traceback.print_exc()
