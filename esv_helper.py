"""
ESV Bible helper module.
Fetches, caches, and navigates the English Standard Version (ESV) Bible text
using the open-source Bolls Life Bible API with local disk caching.
"""

import os
import re
import json
import logging
import requests
from typing import Optional, Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'esv_cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 66 Books of the Bible in canonical Protestant order
BOOKS = [
    # Old Testament (39 books)
    # The Law (Pentateuch)
    {"id": 1, "name": "Genesis", "testament": "OT", "section": "The Law", "chapters": 50},
    {"id": 2, "name": "Exodus", "testament": "OT", "section": "The Law", "chapters": 40},
    {"id": 3, "name": "Leviticus", "testament": "OT", "section": "The Law", "chapters": 27},
    {"id": 4, "name": "Numbers", "testament": "OT", "section": "The Law", "chapters": 36},
    {"id": 5, "name": "Deuteronomy", "testament": "OT", "section": "The Law", "chapters": 34},
    # Historical Books
    {"id": 6, "name": "Joshua", "testament": "OT", "section": "History", "chapters": 24},
    {"id": 7, "name": "Judges", "testament": "OT", "section": "History", "chapters": 21},
    {"id": 8, "name": "Ruth", "testament": "OT", "section": "History", "chapters": 4},
    {"id": 9, "name": "1 Samuel", "testament": "OT", "section": "History", "chapters": 31},
    {"id": 10, "name": "2 Samuel", "testament": "OT", "section": "History", "chapters": 24},
    {"id": 11, "name": "1 Kings", "testament": "OT", "section": "History", "chapters": 22},
    {"id": 12, "name": "2 Kings", "testament": "OT", "section": "History", "chapters": 25},
    {"id": 13, "name": "1 Chronicles", "testament": "OT", "section": "History", "chapters": 29},
    {"id": 14, "name": "2 Chronicles", "testament": "OT", "section": "History", "chapters": 36},
    {"id": 15, "name": "Ezra", "testament": "OT", "section": "History", "chapters": 10},
    {"id": 16, "name": "Nehemiah", "testament": "OT", "section": "History", "chapters": 13},
    {"id": 17, "name": "Esther", "testament": "OT", "section": "History", "chapters": 10},
    # Poetry & Wisdom
    {"id": 18, "name": "Job", "testament": "OT", "section": "Poetry & Wisdom", "chapters": 42},
    {"id": 19, "name": "Psalms", "testament": "OT", "section": "Poetry & Wisdom", "chapters": 150},
    {"id": 20, "name": "Proverbs", "testament": "OT", "section": "Poetry & Wisdom", "chapters": 31},
    {"id": 21, "name": "Ecclesiastes", "testament": "OT", "section": "Poetry & Wisdom", "chapters": 12},
    {"id": 22, "name": "Song of Solomon", "testament": "OT", "section": "Poetry & Wisdom", "chapters": 8},
    # Major Prophets
    {"id": 23, "name": "Isaiah", "testament": "OT", "section": "Major Prophets", "chapters": 66},
    {"id": 24, "name": "Jeremiah", "testament": "OT", "section": "Major Prophets", "chapters": 52},
    {"id": 25, "name": "Lamentations", "testament": "OT", "section": "Major Prophets", "chapters": 5},
    {"id": 26, "name": "Ezekiel", "testament": "OT", "section": "Major Prophets", "chapters": 48},
    {"id": 27, "name": "Daniel", "testament": "OT", "section": "Major Prophets", "chapters": 12},
    # Minor Prophets
    {"id": 28, "name": "Hosea", "testament": "OT", "section": "Minor Prophets", "chapters": 14},
    {"id": 29, "name": "Joel", "testament": "OT", "section": "Minor Prophets", "chapters": 3},
    {"id": 30, "name": "Amos", "testament": "OT", "section": "Minor Prophets", "chapters": 9},
    {"id": 31, "name": "Obadiah", "testament": "OT", "section": "Minor Prophets", "chapters": 1},
    {"id": 32, "name": "Jonah", "testament": "OT", "section": "Minor Prophets", "chapters": 4},
    {"id": 33, "name": "Micah", "testament": "OT", "section": "Minor Prophets", "chapters": 7},
    {"id": 34, "name": "Nahum", "testament": "OT", "section": "Minor Prophets", "chapters": 3},
    {"id": 35, "name": "Habakkuk", "testament": "OT", "section": "Minor Prophets", "chapters": 3},
    {"id": 36, "name": "Zephaniah", "testament": "OT", "section": "Minor Prophets", "chapters": 3},
    {"id": 37, "name": "Haggai", "testament": "OT", "section": "Minor Prophets", "chapters": 2},
    {"id": 38, "name": "Zechariah", "testament": "OT", "section": "Minor Prophets", "chapters": 14},
    {"id": 39, "name": "Malachi", "testament": "OT", "section": "Minor Prophets", "chapters": 4},

    # New Testament (27 books)
    # Gospels & Acts
    {"id": 40, "name": "Matthew", "testament": "NT", "section": "Gospels & Acts", "chapters": 28},
    {"id": 41, "name": "Mark", "testament": "NT", "section": "Gospels & Acts", "chapters": 16},
    {"id": 42, "name": "Luke", "testament": "NT", "section": "Gospels & Acts", "chapters": 24},
    {"id": 43, "name": "John", "testament": "NT", "section": "Gospels & Acts", "chapters": 21},
    {"id": 44, "name": "Acts", "testament": "NT", "section": "Gospels & Acts", "chapters": 28},
    # Paul's Epistles
    {"id": 45, "name": "Romans", "testament": "NT", "section": "Paul's Epistles", "chapters": 16},
    {"id": 46, "name": "1 Corinthians", "testament": "NT", "section": "Paul's Epistles", "chapters": 16},
    {"id": 47, "name": "2 Corinthians", "testament": "NT", "section": "Paul's Epistles", "chapters": 13},
    {"id": 48, "name": "Galatians", "testament": "NT", "section": "Paul's Epistles", "chapters": 6},
    {"id": 49, "name": "Ephesians", "testament": "NT", "section": "Paul's Epistles", "chapters": 6},
    {"id": 50, "name": "Philippians", "testament": "NT", "section": "Paul's Epistles", "chapters": 4},
    {"id": 51, "name": "Colossians", "testament": "NT", "section": "Paul's Epistles", "chapters": 4},
    {"id": 52, "name": "1 Thessalonians", "testament": "NT", "section": "Paul's Epistles", "chapters": 5},
    {"id": 53, "name": "2 Thessalonians", "testament": "NT", "section": "Paul's Epistles", "chapters": 3},
    {"id": 54, "name": "1 Timothy", "testament": "NT", "section": "Paul's Epistles", "chapters": 6},
    {"id": 55, "name": "2 Timothy", "testament": "NT", "section": "Paul's Epistles", "chapters": 4},
    {"id": 56, "name": "Titus", "testament": "NT", "section": "Paul's Epistles", "chapters": 3},
    {"id": 57, "name": "Philemon", "testament": "NT", "section": "Paul's Epistles", "chapters": 1},
    # General Epistles & Prophecy
    {"id": 58, "name": "Hebrews", "testament": "NT", "section": "General Epistles", "chapters": 13},
    {"id": 59, "name": "James", "testament": "NT", "section": "General Epistles", "chapters": 5},
    {"id": 60, "name": "1 Peter", "testament": "NT", "section": "General Epistles", "chapters": 5},
    {"id": 61, "name": "2 Peter", "testament": "NT", "section": "General Epistles", "chapters": 3},
    {"id": 62, "name": "1 John", "testament": "NT", "section": "General Epistles", "chapters": 5},
    {"id": 63, "name": "2 John", "testament": "NT", "section": "General Epistles", "chapters": 1},
    {"id": 64, "name": "3 John", "testament": "NT", "section": "General Epistles", "chapters": 1},
    {"id": 65, "name": "Jude", "testament": "NT", "section": "General Epistles", "chapters": 1},
    {"id": 66, "name": "Revelation", "testament": "NT", "section": "Prophecy", "chapters": 22},
]

BOOK_BY_ID = {b["id"]: b for b in BOOKS}
BOOK_BY_NAME = {b["name"].lower(): b for b in BOOKS}

# Common abbreviations mapping
ABBREVIATIONS = {
    "gen": "Genesis", "ge": "Genesis", "gn": "Genesis",
    "ex": "Exodus", "exod": "Exodus", "exo": "Exodus",
    "lev": "Leviticus", "le": "Leviticus", "lv": "Leviticus",
    "num": "Numbers", "nu": "Numbers", "nm": "Numbers", "nb": "Numbers",
    "deut": "Deuteronomy", "de": "Deuteronomy", "dt": "Deuteronomy",
    "josh": "Joshua", "jos": "Joshua", "jsh": "Joshua",
    "judg": "Judges", "jdg": "Judges", "jg": "Judges", "jdgs": "Judges",
    "ruth": "Ruth", "ru": "Ruth", "rth": "Ruth",
    "1sam": "1 Samuel", "1 sam": "1 Samuel", "1s": "1 Samuel", "1 sa": "1 Samuel",
    "2sam": "2 Samuel", "2 sam": "2 Samuel", "2s": "2 Samuel", "2 sa": "2 Samuel",
    "1ki": "1 Kings", "1kgs": "1 Kings", "1 kgs": "1 Kings", "1 kings": "1 Kings", "1k": "1 Kings",
    "2ki": "2 Kings", "2kgs": "2 Kings", "2 kgs": "2 Kings", "2 kings": "2 Kings", "2k": "2 Kings",
    "1chron": "1 Chronicles", "1chr": "1 Chronicles", "1 chr": "1 Chronicles", "1 chron": "1 Chronicles",
    "2chron": "2 Chronicles", "2chr": "2 Chronicles", "2 chr": "2 Chronicles", "2 chron": "2 Chronicles",
    "ezra": "Ezra", "ezr": "Ezra",
    "neh": "Nehemiah", "ne": "Nehemiah",
    "est": "Esther", "esth": "Esther", "es": "Esther",
    "job": "Job", "jb": "Job",
    "ps": "Psalms", "psa": "Psalms", "psalm": "Psalms", "psalms": "Psalms", "pss": "Psalms",
    "prov": "Proverbs", "prv": "Proverbs", "pro": "Proverbs", "pr": "Proverbs",
    "eccles": "Ecclesiastes", "ecc": "Ecclesiastes", "eccl": "Ecclesiastes", "ec": "Ecclesiastes",
    "song": "Song of Solomon", "songs": "Song of Solomon", "sos": "Song of Solomon", "canticles": "Song of Solomon",
    "isa": "Isaiah", "is": "Isaiah",
    "jer": "Jeremiah", "je": "Jeremiah", "jr": "Jeremiah",
    "lam": "Lamentations", "la": "Lamentations",
    "ezek": "Ezekiel", "eze": "Ezekiel", "ez": "Ezekiel",
    "dan": "Daniel", "da": "Daniel", "dn": "Daniel",
    "hos": "Hosea", "ho": "Hosea",
    "joel": "Joel", "joe": "Joel", "jl": "Joel",
    "amos": "Amos", "am": "Amos",
    "obad": "Obadiah", "ob": "Obadiah", "oba": "Obadiah",
    "jonah": "Jonah", "jon": "Jonah", "jnh": "Jonah",
    "mic": "Micah", "micah": "Micah", "mc": "Micah",
    "nah": "Nahum", "na": "Nahum",
    "hab": "Habakkuk", "hb": "Habakkuk",
    "zeph": "Zephaniah", "zep": "Zephaniah", "zp": "Zephaniah",
    "hag": "Haggai", "hg": "Haggai",
    "zech": "Zechariah", "zec": "Zechariah", "zc": "Zechariah",
    "mal": "Malachi", "ml": "Malachi",
    "matt": "Matthew", "mat": "Matthew", "mt": "Matthew",
    "mark": "Mark", "mk": "Mark", "mrk": "Mark",
    "luke": "Luke", "lk": "Luke", "luk": "Luke",
    "john": "John", "jn": "John", "jhn": "John",
    "acts": "Acts", "act": "Acts", "ac": "Acts",
    "rom": "Romans", "ro": "Romans", "rm": "Romans",
    "1cor": "1 Corinthians", "1 cor": "1 Corinthians", "1co": "1 Corinthians", "1 co": "1 Corinthians",
    "2cor": "2 Corinthians", "2 cor": "2 Corinthians", "2co": "2 Corinthians", "2 co": "2 Corinthians",
    "gal": "Galatians", "ga": "Galatians",
    "eph": "Ephesians", "ep": "Ephesians",
    "phil": "Philippians", "php": "Philippians", "pp": "Philippians",
    "col": "Colossians", "co": "Colossians",
    "1thess": "1 Thessalonians", "1 thess": "1 Thessalonians", "1th": "1 Thessalonians", "1 th": "1 Thessalonians",
    "2thess": "2 Thessalonians", "2 thess": "2 Thessalonians", "2th": "2 Thessalonians", "2 th": "2 Thessalonians",
    "1tim": "1 Timothy", "1 tim": "1 Timothy", "1ti": "1 Timothy", "1 ti": "1 Timothy",
    "2tim": "2 Timothy", "2 tim": "2 Timothy", "2ti": "2 Timothy", "2 ti": "2 Timothy",
    "titus": "Titus", "tit": "Titus", "ti": "Titus",
    "philem": "Philemon", "phm": "Philemon", "pm": "Philemon",
    "heb": "Hebrews", "he": "Hebrews",
    "james": "James", "jas": "James", "jm": "James",
    "1pet": "1 Peter", "1 pet": "1 Peter", "1pe": "1 Peter", "1 pe": "1 Peter", "1p": "1 Peter",
    "2pet": "2 Peter", "2 pet": "2 Peter", "2pe": "2 Peter", "2 pe": "2 Peter", "2p": "2 Peter",
    "1jn": "1 John", "1 jn": "1 John", "1john": "1 John", "1 john": "1 John", "1j": "1 John",
    "2jn": "2 John", "2 jn": "2 John", "2john": "2 John", "2 john": "2 John", "2j": "2 John",
    "3jn": "3 John", "3 jn": "3 John", "3john": "3 John", "3 john": "3 John", "3j": "3 John",
    "jude": "Jude", "jud": "Jude", "jd": "Jude",
    "rev": "Revelation", "re": "Revelation", "revelation": "Revelation", "revelations": "Revelation",
}

# In-memory LRU-like cache
_memory_cache: Dict[str, Any] = {}

HEADERS = {
    'User-Agent': 'CPCNewHavenBibleReader/1.0 (https://cpcnewhaven.org; contact@cpcnewhaven.org)'
}


def find_book(query: str) -> Optional[Dict[str, Any]]:
    """Look up a book by ID, full name, or abbreviation."""
    if not query:
        return None
    
    # Check if integer ID
    try:
        b_id = int(query)
        if b_id in BOOK_BY_ID:
            return BOOK_BY_ID[b_id]
    except (ValueError, TypeError):
        pass

    clean = query.strip().lower()
    # Direct match
    if clean in BOOK_BY_NAME:
        return BOOK_BY_NAME[clean]
    
    # Abbreviation match
    if clean in ABBREVIATIONS:
        canonical = ABBREVIATIONS[clean].lower()
        if canonical in BOOK_BY_NAME:
            return BOOK_BY_NAME[canonical]
            
    # Starts with
    for name, book in BOOK_BY_NAME.items():
        if name.startswith(clean):
            return book

    return None


def parse_passage_reference(ref: str) -> Tuple[Optional[Dict[str, Any]], int, Optional[int], Optional[int]]:
    """
    Parse a reference string such as "John 3", "John 3:16", "Romans 8:28-39", or "1 Cor 13".
    Returns (book_dict, chapter, start_verse, end_verse).
    """
    if not ref:
        return None, 1, None, None

    ref = ref.strip()
    # Match patterns like: [1-3]? [A-Za-z ]+ [0-9]+(:[0-9]+(-[0-9]+)?)?
    match = re.match(r'^((?:[1-3]\s+)?[A-Za-z\s]+?)\s*(\d+)(?:\s*[:.]\s*(\d+)(?:\s*-\s*(\d+))?)?$', ref)
    if match:
        book_part = match.group(1).strip()
        chapter_str = match.group(2)
        start_v_str = match.group(3)
        end_v_str = match.group(4)

        book = find_book(book_part)
        chapter = int(chapter_str) if chapter_str else 1
        start_v = int(start_v_str) if start_v_str else None
        end_v = int(end_v_str) if end_v_str else None
        return book, chapter, start_v, end_v

    # Fallback: Maybe user just typed a book name like "Genesis"
    book = find_book(ref)
    if book:
        return book, 1, None, None

    return None, 1, None, None


def get_prev_and_next(book_id: int, chapter: int) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Calculate the previous and next chapter metadata across the entire canon."""
    current_book = BOOK_BY_ID.get(book_id)
    if not current_book:
        return None, None

    # Previous chapter
    if chapter > 1:
        prev_info = {"book_id": book_id, "book_name": current_book["name"], "chapter": chapter - 1}
    elif book_id > 1:
        prev_book = BOOK_BY_ID[book_id - 1]
        prev_info = {"book_id": prev_book["id"], "book_name": prev_book["name"], "chapter": prev_book["chapters"]}
    else:
        prev_info = None

    # Next chapter
    if chapter < current_book["chapters"]:
        next_info = {"book_id": book_id, "book_name": current_book["name"], "chapter": chapter + 1}
    elif book_id < 66:
        next_book = BOOK_BY_ID[book_id + 1]
        next_info = {"book_id": next_book["id"], "book_name": next_book["name"], "chapter": 1}
    else:
        next_info = None

    return prev_info, next_info


def get_chapter_text(book_id: int, chapter: int) -> Dict[str, Any]:
    """
    Fetch chapter text from cache or Bolls Life ESV API.
    Returns structured chapter data.
    """
    book = BOOK_BY_ID.get(book_id)
    if not book:
        return {"success": False, "error": f"Invalid book ID: {book_id}"}

    # Clamp chapter
    chapter = max(1, min(chapter, book["chapters"]))

    cache_key = f"{book_id}_{chapter}"
    if cache_key in _memory_cache:
        data = _memory_cache[cache_key]
        prev_info, next_info = get_prev_and_next(book_id, chapter)
        return {
            "success": True,
            "book": book,
            "chapter": chapter,
            "verses": data,
            "prev": prev_info,
            "next": next_info,
            "source": "memory"
        }

    # Check disk cache
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                verses = json.load(f)
            _memory_cache[cache_key] = verses
            prev_info, next_info = get_prev_and_next(book_id, chapter)
            return {
                "success": True,
                "book": book,
                "chapter": chapter,
                "verses": verses,
                "prev": prev_info,
                "next": next_info,
                "source": "disk"
            }
        except Exception as e:
            logger.warning(f"Failed to read disk cache for {cache_key}: {e}")

    # Fetch from Bolls Life API
    url = f"https://bolls.life/get-text/ESV/{book_id}/{chapter}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        raw_verses = resp.json()

        verses = []
        for v in raw_verses:
            verses.append({
                "verse": v.get("verse"),
                "text": v.get("text", "").strip()
            })

        # Save to memory and disk cache
        _memory_cache[cache_key] = verses
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(verses, f)
        except Exception as e:
            logger.warning(f"Failed to write disk cache for {cache_key}: {e}")

        prev_info, next_info = get_prev_and_next(book_id, chapter)
        return {
            "success": True,
            "book": book,
            "chapter": chapter,
            "verses": verses,
            "prev": prev_info,
            "next": next_info,
            "source": "network"
        }
    except Exception as e:
        logger.error(f"Error fetching {book['name']} {chapter} from ESV API: {e}")
        return {
            "success": False,
            "book": book,
            "chapter": chapter,
            "error": f"Could not load {book['name']} {chapter}. Please check your connection or try again."
        }


def search_esv(query: str, limit: int = 50) -> Dict[str, Any]:
    """Search ESV text for keywords via Bolls Life API."""
    clean_query = query.strip()
    if not clean_query:
        return {"success": False, "error": "Search query cannot be empty"}

    url = f"https://bolls.life/search/ESV/?search={requests.utils.quote(clean_query)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        results_raw = resp.json()

        results = []
        for r in results_raw[:limit]:
            b_id = r.get("book")
            b_name = BOOK_BY_ID.get(b_id, {}).get("name", f"Book {b_id}")
            results.append({
                "book_id": b_id,
                "book_name": b_name,
                "chapter": r.get("chapter"),
                "verse": r.get("verse"),
                "text": r.get("text", "")
            })

        return {
            "success": True,
            "query": clean_query,
            "total_matches": len(results_raw),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error searching ESV for '{clean_query}': {e}")
        return {
            "success": False,
            "query": clean_query,
            "error": "Failed to complete search. Please try again later."
        }
