from app import app, db
from models import BibleBook
from sqlalchemy import inspect

def seed_books():
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        # Check if books exist
        if BibleBook.query.first():
            print("Bible books already seeded.")
            return

        books = [
            ("Genesis", "OT", 1), ("Exodus", "OT", 2), ("Leviticus", "OT", 3), ("Numbers", "OT", 4), ("Deuteronomy", "OT", 5),
            ("Joshua", "OT", 6), ("Judges", "OT", 7), ("Ruth", "OT", 8), ("1 Samuel", "OT", 9), ("2 Samuel", "OT", 10),
            ("1 Kings", "OT", 11), ("2 Kings", "OT", 12), ("1 Chronicles", "OT", 13), ("2 Chronicles", "OT", 14), ("Ezra", "OT", 15),
            ("Nehemiah", "OT", 16), ("Esther", "OT", 17), ("Job", "OT", 18), ("Psalms", "OT", 19), ("Proverbs", "OT", 20),
            ("Ecclesiastes", "OT", 21), ("Song of Solomon", "OT", 22), ("Isaiah", "OT", 23), ("Jeremiah", "OT", 24), ("Lamentations", "OT", 25),
            ("Ezekiel", "OT", 26), ("Daniel", "OT", 27), ("Hosea", "OT", 28), ("Joel", "OT", 29), ("Amos", "OT", 30),
            ("Obadiah", "OT", 31), ("Jonah", "OT", 32), ("Micah", "OT", 33), ("Nahum", "OT", 34), ("Habakkuk", "OT", 35),
            ("Zephaniah", "OT", 36), ("Haggai", "OT", 37), ("Zechariah", "OT", 38), ("Malachi", "OT", 39),
            ("Matthew", "NT", 40), ("Mark", "NT", 41), ("Luke", "NT", 42), ("John", "NT", 43), ("Acts", "NT", 44),
            ("Romans", "NT", 45), ("1 Corinthians", "NT", 46), ("2 Corinthians", "NT", 47), ("Galatians", "NT", 48), ("Ephesians", "NT", 49),
            ("Philippians", "NT", 50), ("Colossians", "NT", 51), ("1 Thessalonians", "NT", 52), ("2 Thessalonians", "NT", 53), ("1 Timothy", "NT", 54),
            ("2 Timothy", "NT", 55), ("Titus", "NT", 56), ("Philemon", "NT", 57), ("Hebrews", "NT", 58), ("James", "NT", 59),
            ("1 Peter", "NT", 60), ("2 Peter", "NT", 61), ("1 John", "NT", 62), ("2 John", "NT", 63), ("3 John", "NT", 64),
            ("Jude", "NT", 65), ("Revelation", "NT", 66)
        ]

        for name, testament, order in books:
            db.session.add(BibleBook(name=name, testament=testament, sort_order=order))
        
        db.session.commit()
        print("Seeded 66 Bible books.")

        # Trigger schema update for existing tables
        from app import ensure_db_columns
        ensure_db_columns()
        print("Ensured DB columns.")

if __name__ == "__main__":
    seed_books()
