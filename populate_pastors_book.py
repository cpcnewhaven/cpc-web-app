from app import app, db, SiteContent
from datetime import datetime

def populate_pastors_book():
    with app.app_context():
        data = {
            'pastors_book_active': 'True',
            'pastors_book_label': "Pastor’s Book Pick",
            'pastors_book_title': 'Life Together',
            'pastors_book_author': 'Dietrich Bonhoeffer',
            'pastors_book_description': "A modern classic, we're treading into deep waters with this one! Written by pastor-theologian and martyr, Life Together is Bonhoeffer's vision for the Christian life, both individually and communally. Copies in the foyer — suggested donation of $15.",
            'pastors_book_image_url': 'https://m.media-amazon.com/images/I/41VLz4wzqrL._SY445_SX342_FMwebp_.jpg',
            'pastors_book_cta_text': 'Suggested donation of $15',
            'pastors_book_cta_link': '',
        }
        
        for key, value in data.items():
            content = SiteContent.query.filter_by(key=key).first()
            if content:
                content.value = value
                content.updated_at = datetime.utcnow()
                print(f"Updated {key}")
            else:
                new_content = SiteContent(key=key, value=value)
                db.session.add(new_content)
                print(f"Created {key}")
        
        db.session.commit()
        print("Successfully populated Pastor's Book Pick data.")

if __name__ == '__main__':
    populate_pastors_book()
