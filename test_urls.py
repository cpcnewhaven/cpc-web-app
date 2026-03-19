from app import app, admin
from flask import url_for
with app.test_request_context():
    print([v.endpoint for v in admin._views])
    try:
        print(url_for('announcement.edit_view', id=1))
    except Exception as e:
        print("ERROR:", e)
