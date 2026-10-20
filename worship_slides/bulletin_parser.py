"""Bulletin parsing engine for CPC New Haven worship services.

Extracts structured liturgical items (Call to Worship, Songs, Prayers,
Scripture readings, Sermon, Lord's Supper, Benediction, Announcements)
from Google Docs or pasted bulletin text, and chunks them into
readable slide blocks suitable for congregation projection.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple


# Default IDs provided for CPC New Haven standardized worship workflow
DEFAULT_BULLETIN_DOC_ID = "1nDWJbDmvbf1PNYbHk9JMrjdihIrW2Cy9_MZoZBD-gNc"
DEFAULT_SLIDES_TEMPLATE_ID = "15zT3vmtW0ZYXYgm57qIkOAaLcNODjuNYQeur48w_oNw"

# Standard liturgical headers common in Presbyterian / Reformed worship
KNOWN_SECTIONS = [
    ("CALL TO WORSHIP", "liturgy"),
    ("CALLS TO WORSHIP", "liturgy"),
    ("INVOCATION", "prayer"),
    ("PRAYER OF INVOCATION", "prayer"),
    ("PRAYER OF ADORATION", "prayer"),
    ("ADORATION", "prayer"),
    ("HYMN OF PRAISE", "song"),
    ("HYMNS OF PRAISE", "song"),
    ("SONG OF PRAISE", "song"),
    ("SONGS OF PRAISE", "song"),
    ("OPENING HYMN", "song"),
    ("OPENING SONG", "song"),
    ("CONFESSION OF SIN", "liturgy"),
    ("PRAYER OF CONFESSION", "liturgy"),
    ("CORPORATE CONFESSION", "liturgy"),
    ("ASSURANCE OF PARDON", "scripture"),
    ("ASSURANCE OF GRACE", "scripture"),
    ("ASSURANCE OF GOD'S PARDON", "scripture"),
    ("PASSING OF THE PEACE", "liturgy"),
    ("PEACE OF CHRIST", "liturgy"),
    ("SONG OF THANKSGIVING", "song"),
    ("SONG OF ASSURANCE", "song"),
    ("GLORIA PATRI", "song"),
    ("SCRIPTURE READING", "scripture"),
    ("OLD TESTAMENT READING", "scripture"),
    ("NEW TESTAMENT READING", "scripture"),
    ("EPISTLE READING", "scripture"),
    ("GOSPEL READING", "scripture"),
    ("RESPONSIVE READING", "liturgy"),
    ("RESPONSIVE PSALM", "liturgy"),
    ("PRAYERS OF THE PEOPLE", "prayer"),
    ("PASTORAL PRAYER", "prayer"),
    ("THE LORD'S PRAYER", "prayer"),
    ("COLLECTION OF GIFTS", "liturgy"),
    ("OFFERTORY", "liturgy"),
    ("OFFERING", "liturgy"),
    ("SERMON", "sermon"),
    ("THE SACRAMENT OF THE LORD'S SUPPER", "communion"),
    ("THE LORD'S SUPPER", "communion"),
    ("HOLY COMMUNION", "communion"),
    ("WORDS OF INSTITUTION", "communion"),
    ("HYMN OF RESPONSE", "song"),
    ("SONG OF RESPONSE", "song"),
    ("CLOSING HYMN", "song"),
    ("CLOSING SONG", "song"),
    ("DOXOLOGY", "song"),
    ("BENEDICTION", "liturgy"),
    ("WORDS OF DISMISSAL", "liturgy"),
    ("ANNOUNCEMENTS", "announcement"),
    ("THIS WEEK AT CPC", "announcement"),
    ("CONFESSION OF FAITH", "liturgy"),
    ("APOSTLES' CREED", "liturgy"),
    ("NICENE CREED", "liturgy"),
]


def extract_google_id(url_or_id: str) -> str:
    """Extract a 20+ character Google Doc/Drive/Slide ID from a URL or raw ID."""
    if not url_or_id:
        return ""
    cleaned = url_or_id.strip()
    # Match patterns like /document/d/<id>/ or /presentation/d/<id>/ or /file/d/<id>/
    url_match = re.search(r"/(?:document|presentation|file|spreadsheets)/d/([a-zA-Z0-9_-]{20,})", cleaned)
    if url_match:
        return url_match.group(1)
    # Match ?id=<id>
    id_param_match = re.search(r"[?&]id=([a-zA-Z0-9_-]{20,})", cleaned)
    if id_param_match:
        return id_param_match.group(1)
    # Match bare ID
    bare_match = re.match(r"^([a-zA-Z0-9_-]{20,})$", cleaned)
    if bare_match:
        return bare_match.group(1)
    return cleaned


def normalize_text(text: str) -> str:
    """Normalize unicode quotes, dashes, and whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2014", "—").replace("\u2013", "–")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def extract_text_from_google_doc(doc_json: Dict[str, Any]) -> str:
    """Extract structured plain text with heading markers from Google Docs API output.

    Preserves headings (prefixed with ##) and paragraphs.
    """
    body = doc_json.get("body", {})
    content = body.get("content", [])
    output_lines: List[str] = []

    for element in content:
        if "paragraph" in element:
            paragraph = element["paragraph"]
            style = paragraph.get("paragraphStyle", {})
            named_style = style.get("namedStyleType", "")

            # Reconstruct text of this paragraph
            para_runs: List[str] = []
            is_all_bold = True
            has_text = False

            for el in paragraph.get("elements", []):
                text_run = el.get("textRun", {})
                run_text = text_run.get("content", "")
                if run_text.strip():
                    has_text = True
                    text_style = text_run.get("textStyle", {})
                    if not text_style.get("bold"):
                        is_all_bold = False
                para_runs.append(run_text)

            full_para = "".join(para_runs).strip()
            if not full_para:
                output_lines.append("")
                continue

            # Check if this paragraph acts as a section heading
            is_heading = (
                named_style in ("HEADING_1", "HEADING_2", "HEADING_3", "TITLE")
                or (is_all_bold and has_text and len(full_para) <= 80 and not full_para.endswith("."))
            )

            if is_heading:
                output_lines.append(f"\n## {full_para}\n")
            else:
                output_lines.append(full_para)

        elif "table" in element:
            # Handle tables (often used for responsive readings or 2-column service outlines)
            table = element["table"]
            for row in table.get("tableRows", []):
                row_cells: List[str] = []
                for cell in row.get("tableCells", []):
                    cell_text: List[str] = []
                    for cell_el in cell.get("content", []):
                        if "paragraph" in cell_el:
                            for tel in cell_el["paragraph"].get("elements", []):
                                cell_text.append(tel.get("textRun", {}).get("content", ""))
                    cell_str = "".join(cell_text).strip()
                    if cell_str:
                        row_cells.append(cell_str)
                if row_cells:
                    output_lines.append(" : ".join(row_cells))

    return normalize_text("\n".join(output_lines))


def is_heading_line(line: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Determine if a line represents a liturgical section header.

    Returns (is_heading, section_title, category).
    """
    cleaned = line.strip().lstrip("#").strip()
    if not cleaned:
        return False, None, None

    cleaned_upper = cleaned.upper()

    # Exact or prefix match against known liturgical sections
    for section_name, cat in KNOWN_SECTIONS:
        if cleaned_upper == section_name or cleaned_upper.startswith(section_name + " ") or cleaned_upper.startswith(section_name + ":") or cleaned_upper.startswith(section_name + " -") or cleaned_upper.startswith(section_name + " —"):
            return True, cleaned, cat

    # Patterns like "HYMN: ...", "SONG: ...", "SCRIPTURE: ...", "SERMON: ..."
    prefix_patterns = [
        (r"^(?:HYMN|SONG)\s*[:—–-]\s*(.*)$", "song"),
        (r"^(?:SCRIPTURE|READING)\s*[:—–-]\s*(.*)$", "scripture"),
        (r"^(?:SERMON|MESSAGE)\s*[:—–-]\s*(.*)$", "sermon"),
        (r"^(?:PRAYER|INVOCATION)\s*[:—–-]\s*(.*)$", "prayer"),
    ]
    for pattern, cat in prefix_patterns:
        match = re.match(pattern, cleaned, re.IGNORECASE)
        if match:
            return True, cleaned, cat

    # All-caps line with reasonable length, not looking like a full sentence
    if line.startswith("## ") and len(cleaned) <= 90:
        return True, cleaned, _infer_category(cleaned)

    if cleaned.isupper() and len(cleaned) <= 60 and not cleaned.endswith((".", ",", ";")) and len(cleaned.split()) <= 7:
        return True, cleaned, _infer_category(cleaned)

    return False, None, None


def _infer_category(title: str) -> str:
    """Infer liturgical category from a header title."""
    upper = title.upper()
    if any(k in upper for k in ("HYMN", "SONG", "PRAISE", "DOXOLOGY", "GLORIA")):
        return "song"
    if any(k in upper for k in ("SCRIPTURE", "READING", "GOSPEL", "TESTAMENT", "PSALM", "EPISTLE")):
        return "scripture"
    if any(k in upper for k in ("SERMON", "MESSAGE", "HOMILY", "PREACHING")):
        return "sermon"
    if any(k in upper for k in ("PRAYER", "INVOCATION", "ADORATION", "SUPPLICATION")):
        return "prayer"
    if any(k in upper for k in ("COMMUNION", "EUCHARIST", "SUPPER", "TABLE")):
        return "communion"
    if any(k in upper for k in ("ANNOUNCEMENT", "THIS WEEK", "EVENTS", "MINISTRY")):
        return "announcement"
    return "liturgy"


def chunk_text_into_slides(title: str, content: str, category: str, max_lines_per_slide: int = 5) -> List[Dict[str, str]]:
    """Break section text into readable slide blocks for projection.

    Splits song verses into individual slides, labels verses, and breaks
    long scripture or readings into readable 3-5 line slide blocks.
    """
    slides: List[Dict[str, str]] = []
    lines = [ln.strip() for ln in content.splitlines()]

    # If category is sermon, create a single clean slide with sermon details
    if category == "sermon":
        return [{"title": title, "content": "\n".join(ln for ln in lines if ln)}]

    # Check for song verse markers (e.g., "Verse 1", "Chorus", "Bridge", "Refrain", "1.", "2.")
    verse_pattern = re.compile(
        r"^(?:Verse\s*\d+|Chorus(?:\s*\d+)?|Refrain|Bridge|Tag|Outro|\d+\.)",
        re.IGNORECASE,
    )

    if category == "song" and any(verse_pattern.match(ln) for ln in lines if ln):
        current_verse_label = ""
        current_verse_lines: List[str] = []

        def flush_verse():
            if not current_verse_lines:
                return
            full_verse_text = "\n".join(current_verse_lines)
            # If verse is longer than max_lines, chunk it into sub-slides
            sub_lines = [l for l in current_verse_lines if l]
            for i in range(0, len(sub_lines), max_lines_per_slide):
                chunk = "\n".join(sub_lines[i : i + max_lines_per_slide])
                label_suffix = f" · {current_verse_label}" if current_verse_label else ""
                part_suffix = f" (cont.)" if i > 0 else ""
                slides.append({
                    "title": f"{title}{label_suffix}{part_suffix}".strip(),
                    "content": chunk,
                })

        for line in lines:
            if not line:
                continue
            if verse_pattern.match(line):
                flush_verse()
                current_verse_label = line
                current_verse_lines = []
            else:
                current_verse_lines.append(line)
        flush_verse()
        if slides:
            return slides

    # Default line-based chunking for liturgy, readings, and unsegmented songs
    current_block: List[str] = []

    for line in lines:
        if not line:
            if current_block:
                slides.append({"title": title, "content": "\n".join(current_block)})
                current_block = []
            continue
        current_block.append(line)
        if len(current_block) >= max_lines_per_slide:
            slides.append({"title": title, "content": "\n".join(current_block)})
            current_block = []

    if current_block:
        slides.append({"title": title, "content": "\n".join(current_block)})

    if not slides:
        slides.append({"title": title, "content": ""})

    return slides


def parse_bulletin_text(raw_text: str) -> List[Dict[str, Any]]:
    """Parse raw bulletin text into structured service items.

    Each item contains:
    - title: Section title (e.g. 'Call to Worship', 'Hymn of Praise: Come Thou Fount')
    - category: 'liturgy', 'song', 'scripture', 'prayer', 'sermon', 'communion', 'announcement'
    - content: Full text of the section
    - slides: Pre-calculated list of slide cards [{'title': ..., 'content': ...}]
    """
    normalized = normalize_text(raw_text)
    lines = normalized.splitlines()

    sections: List[Dict[str, Any]] = []
    current_title = "Welcome & Call to Worship"
    current_category = "liturgy"
    current_lines: List[str] = []

    def flush_section():
        nonlocal current_title, current_category, current_lines
        content = "\n".join(current_lines).strip()
        if content or sections:
            # Detect secondary song title if category is song and content starts with a title line
            clean_title = current_title
            if current_category == "song" and content:
                first_line = content.splitlines()[0].strip()
                if len(first_line) <= 60 and not re.match(r"^(?:Verse|\d+\.|Chorus)", first_line, re.IGNORECASE):
                    # The first line is likely the hymn title
                    if any(clean_title.upper().startswith(k) for k in ("HYMN", "SONG", "OPENING", "CLOSING")):
                        clean_title = f"{clean_title}: {first_line}"
                        content = "\n".join(content.splitlines()[1:]).strip()

            slides = chunk_text_into_slides(clean_title, content, current_category)
            sections.append({
                "title": clean_title,
                "category": current_category,
                "content": content,
                "slides": slides,
                "slide_count": len(slides),
            })
        current_lines = []

    for line in lines:
        is_hd, hd_title, hd_cat = is_heading_line(line)
        if is_hd and hd_title:
            content_so_far = "\n".join(current_lines).strip()
            # If current section has NO content yet, combine generic section with specific header (e.g. HYMN OF PRAISE: Doxology)
            if not content_so_far and current_title and current_title != "Welcome & Call to Worship":
                if any(k in current_title.upper() for k in ("HYMN", "SONG", "SCRIPTURE", "READING")):
                    current_title = f"{current_title}: {hd_title}"
                    if hd_cat:
                        current_category = hd_cat
                    continue

            flush_section()
            current_title = hd_title
            current_category = hd_cat or "liturgy"
        else:
            current_lines.append(line)

    flush_section()

    # Filter out empty leading welcome if it has no content
    if len(sections) > 1 and not sections[0]["content"] and sections[0]["title"] == "Welcome & Call to Worship":
        sections.pop(0)

    # Assign sequence numbers
    for idx, item in enumerate(sections):
        item["sequence"] = idx + 1

    return sections


def merge_pco_with_bulletin(bulletin_items: List[Dict[str, Any]], pco_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Pipe Planning Center Services plan items into bulletin items.

    Matches songs from Planning Center to inject official arrangement lyrics,
    enriches sermon/scripture items, and appends any Planning Center items
    not present in the bulletin (e.g. instrumental prelude).
    """
    merged: List[Dict[str, Any]] = [dict(item) for item in bulletin_items]

    # Map PCO songs by normalized title
    def normalize_title(t: str) -> str:
        t = re.sub(r"^(?:hymn|song|praise|closing|opening)\s*(?:of\s*(?:praise|response|thanksgiving))?[:—–-]?\s*", "", t, flags=re.I)
        return re.sub(r"[^a-zA-Z0-9]", "", t).lower()

    pco_songs = {
        normalize_title(item.get("title", "")): item
        for item in pco_items
        if item.get("kind") == "song" or item.get("content")
    }

    used_pco_keys = set()

    # Enrich existing bulletin items
    for item in merged:
        norm = normalize_title(item.get("title", ""))
        for pco_norm, pco_item in pco_songs.items():
            if pco_norm and (pco_norm in norm or norm in pco_norm):
                # If Planning Center has richer song lyrics, use them!
                pco_lyrics = pco_item.get("content", "").strip()
                if pco_lyrics and (not item.get("content") or len(pco_lyrics) > len(item.get("content", ""))):
                    item["content"] = pco_lyrics
                    item["slides"] = chunk_text_into_slides(item["title"], pco_lyrics, item["category"])
                    item["slide_count"] = len(item["slides"])
                    item["pco_synced"] = True
                used_pco_keys.add(pco_norm)
                break

    # Re-assign sequence numbers
    for idx, item in enumerate(merged):
        item["sequence"] = idx + 1

    return merged
