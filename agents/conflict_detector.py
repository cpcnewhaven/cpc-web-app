#!/usr/bin/env python3
"""
agents/conflict_detector.py  —  Claude Conflict Detector for Chris's BeaverDB Edits
=====================================================================================
Run this AFTER Chris makes changes directly to the database via BeaverDB.
Claude will compare the database state to what the app expects and tell you
exactly what conflicts exist and how to fix them.

Usage:
  python agents/conflict_detector.py
"""

import os
import sys
import json
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import anthropic
except ImportError:
    print("ERROR: pip install anthropic")
    sys.exit(1)

try:
    from sqlalchemy import create_engine, text
except ImportError:
    print("ERROR: sqlalchemy not installed")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    console = Console()
    RICH = True
except ImportError:
    RICH = False
    class _C:
        def print(self, *a, **k): print(*a)
    console = _C()

GLOBAL_ID_TABLES = [
    "announcements", "sermons", "podcast_episodes",
    "podcast_series", "gallery_images", "ongoing_events", "papers"
]

SYSTEM_PROMPT = """You are an expert at detecting database conflicts in a Flask/PostgreSQL web application.

THE SITUATION:
A collaborator named Chris uses a GUI tool called BeaverDB to edit the production database directly.
When Chris does this, he bypasses the app's safety systems:
  1. The GlobalIDCounter — a table that generates unique IDs for all content. If Chris inserts records
     manually with high IDs, the counter can fall behind and the next save from the web app will CRASH
     with a "duplicate primary key" error.
  2. The AuditLog — Chris's changes won't appear in the activity history (/admin/history/).
  3. Data validation — Chris might set wrong data types, missing required fields, etc.

THE GLOBAL ID COUNTER:
  - Stored in the `global_id_counter` table (one row, id=1)
  - The `next_id` column must ALWAYS be higher than the maximum ID in ANY of these tables:
    announcements, sermons, podcast_episodes, podcast_series, gallery_images, ongoing_events, papers
  - If next_id <= max(id) in any of those tables: THE APP WILL CRASH on the next content save

YOUR TASK:
Review the conflict analysis data and explain:
1. Whether the GlobalIDCounter is safe or dangerous
2. Any duplicate records that might confuse users
3. Any data integrity issues (broken links, missing required fields)
4. Records that look like they were inserted by Chris (not through the normal app flow)
5. What to do about each problem — in plain language

BE SPECIFIC: Give exact table names, IDs, and steps to fix each issue.
If everything is fine, say so clearly and confidently.

FORMAT:
🔴 CRITICAL — app will crash, fix immediately
🟡 WARNING — data quality issue, fix soon
✅ SAFE — this area is fine
🔧 HOW TO FIX — specific steps for each issue"""


def collect_conflict_data(conn) -> dict:
    """Deep scan for conflicts, especially from direct DB edits."""
    data = {}
    today = date.today().isoformat()

    # 1. GlobalIDCounter vs actual max IDs
    try:
        counter = conn.execute(
            text("SELECT next_id FROM global_id_counter WHERE id = 1")
        ).scalar()
        data["global_id_counter_value"] = counter
    except:
        data["global_id_counter_value"] = "MISSING"

    max_ids = {}
    for t in GLOBAL_ID_TABLES:
        try:
            max_id = conn.execute(text(f"SELECT MAX(id) FROM {t}")).scalar() or 0
            max_ids[t] = max_id
        except:
            max_ids[t] = 0
    data["max_ids_per_table"] = max_ids

    # IDs that are AT or ABOVE the counter (bypassed it)
    counter_val = data["global_id_counter_value"] if isinstance(data["global_id_counter_value"], int) else 9999999
    bypassed_records = {}
    for t in GLOBAL_ID_TABLES:
        try:
            rows = conn.execute(
                text(f"SELECT id FROM {t} WHERE id >= :c ORDER BY id"),
                {"c": counter_val}
            ).fetchall()
            if rows:
                bypassed_records[t] = [r[0] for r in rows]
        except:
            pass
    data["records_bypassing_counter"] = bypassed_records

    # 2. Duplicate detection (comprehensive)
    dupes = {}

    queries = {
        "announcements_same_title": """
            SELECT LOWER(TRIM(title)), COUNT(*), MIN(id)::text || ' vs ' || MAX(id)::text as ids
            FROM announcements GROUP BY LOWER(TRIM(title)) HAVING COUNT(*) > 1""",
        "sermons_same_date_and_title": """
            SELECT LOWER(TRIM(title)), date::text, COUNT(*), STRING_AGG(id::text, ',') as ids
            FROM sermons GROUP BY LOWER(TRIM(title)), date HAVING COUNT(*) > 1""",
        "sermons_duplicate_episode_numbers": """
            SELECT series_id, episode_number, COUNT(*), STRING_AGG(title, ' / ') as titles
            FROM sermons WHERE series_id IS NOT NULL AND episode_number IS NOT NULL
            GROUP BY series_id, episode_number HAVING COUNT(*) > 1""",
        "podcast_episodes_same_rss_id": """
            SELECT original_id, COUNT(*), STRING_AGG(id::text, ',') as ids
            FROM podcast_episodes WHERE original_id IS NOT NULL
            GROUP BY original_id HAVING COUNT(*) > 1""",
        "podcast_episodes_same_title_in_series": """
            SELECT series_id, LOWER(TRIM(title)), COUNT(*), STRING_AGG(id::text, ',')
            FROM podcast_episodes GROUP BY series_id, LOWER(TRIM(title)) HAVING COUNT(*) > 1""",
    }

    for name, q in queries.items():
        try:
            rows = conn.execute(text(q + " LIMIT 10")).fetchall()
            if rows:
                dupes[name] = [list(r) for r in rows]
        except Exception:
            pass

    data["duplicates"] = dupes

    # 3. Orphaned foreign keys
    orphans = {}
    fk_checks = {
        "sermons with missing series": "SELECT COUNT(*) FROM sermons WHERE series_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sermon_series WHERE id = sermons.series_id)",
        "sermons with missing speaker user": "SELECT COUNT(*) FROM sermons WHERE speaker_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM users WHERE id = sermons.speaker_id)",
        "podcast episodes with missing series": "SELECT COUNT(*) FROM podcast_episodes WHERE series_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM podcast_series WHERE id = podcast_episodes.series_id)",
        "teaching sessions with missing series": "SELECT COUNT(*) FROM teaching_series_sessions WHERE NOT EXISTS (SELECT 1 FROM teaching_series WHERE id = teaching_series_sessions.series_id)",
    }
    for desc, q in fk_checks.items():
        try:
            count = conn.execute(text(q)).scalar()
            if count and count > 0:
                orphans[desc] = count
        except:
            pass
    data["orphaned_fk_counts"] = orphans

    # 4. Records with suspicious data
    suspicious = {}

    # Sermons without a date
    try:
        count = conn.execute(text("SELECT COUNT(*) FROM sermons WHERE date IS NULL")).scalar()
        if count and count > 0:
            suspicious["sermons_missing_date"] = count
    except: pass

    # Announcements without description
    try:
        count = conn.execute(text("SELECT COUNT(*) FROM announcements WHERE description IS NULL OR TRIM(description) = ''")).scalar()
        if count and count > 0:
            suspicious["announcements_missing_description"] = count
    except: pass

    # Active content with dates in the future (entered far ahead)
    try:
        rows = conn.execute(text("""
            SELECT id, title, date_entered::text FROM announcements
            WHERE date_entered > NOW() + INTERVAL '1 day'
            LIMIT 5
        """)).fetchall()
        if rows:
            suspicious["announcements_with_future_entry_date"] = [
                {"id": r[0], "title": r[1], "entered": r[2]} for r in rows
            ]
    except: pass

    data["suspicious_data"] = suspicious

    # 5. Records NOT in audit log (possibly added directly by Chris)
    # If a record was inserted directly, there's no audit_log entry for its creation
    unlogged = {}
    for t, entity_type in [("announcements", "Announcement"), ("sermons", "Sermon")]:
        try:
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM {t} c
                WHERE NOT EXISTS (
                    SELECT 1 FROM audit_log a
                    WHERE a.entity_id = c.id
                    AND a.entity_type = :etype
                    AND a.action = 'created'
                )
            """), {"etype": entity_type}).scalar()
            if count and count > 0:
                unlogged[f"{t}_without_audit_trail"] = count
        except:
            pass
    data["records_without_audit_trail"] = unlogged

    # 6. Recent audit log for context
    try:
        rows = conn.execute(text("""
            SELECT timestamp::text, "user", action, entity_type, entity_id, entity_title
            FROM audit_log ORDER BY timestamp DESC LIMIT 15
        """)).fetchall()
        data["recent_audit_log"] = [
            {"time": r[0], "user": r[1], "action": r[2], "type": r[3], "id": r[4], "title": str(r[5] or "")[:50]}
            for r in rows
        ]
    except:
        data["recent_audit_log"] = []

    return data


def run_agent():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    if RICH:
        console.print(Panel(
            "[bold white]CPC Conflict Detector[/bold white]\n"
            "[dim]Checking for conflicts from Chris's BeaverDB edits...[/dim]",
            border_style="yellow"
        ))

    try:
        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        console.print("  [green]✓ Connected to database[/green]")
    except Exception as e:
        console.print(f"  [red]Cannot connect: {e}[/red]")
        sys.exit(1)

    with engine.connect() as conn:
        console.print("  [dim]Running conflict analysis...[/dim]")
        data = collect_conflict_data(conn)

    console.print("  [dim]Asking Claude to interpret the results...[/dim]\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Here is the conflict analysis data from the CPC church website database.\n\nDATA:\n{json.dumps(data, indent=2, default=str)}\n\nPlease give me a clear conflict report."
            }]
        )

        report = next((b.text for b in response.content if b.type == "text"), "No response.")

        if RICH:
            console.rule("[bold yellow]Conflict Report[/bold yellow]")
            console.print(Markdown(report))
        else:
            print("\n" + "="*60 + "\nCONFLICT REPORT\n" + "="*60)
            print(report)

    except Exception as e:
        console.print(f"[red]Claude error: {e}[/red]")


if __name__ == "__main__":
    run_agent()
