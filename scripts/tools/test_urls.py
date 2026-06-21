# Allow running from any directory by pointing Python at the project root
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app import app, admin
from flask import url_for
with app.test_request_context():
    print([v.endpoint for v in admin._views])
    try:
        print(url_for('announcement.edit_view', id=1))
    except Exception as e:
        print("ERROR:", e)
