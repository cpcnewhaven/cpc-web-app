#!/usr/bin/env python3
"""
agents/db_health_agent.py  —  Claude-Powered Database Health Agent
===================================================================
This agent collects data from your Render PostgreSQL database and sends
it to Claude, which gives you a plain-English health report — like having
a database expert look at your data and tell you what's wrong.

What Claude checks:
  • Are all tables present and populated?
  • Is the GlobalIDCounter in sync? (Critical if Chris edits via BeaverDB)
  • Are there any duplicate records?
  • Are there broken links (orphaned foreign keys)?
  • Is expired content still showing as active?
  • What does the recent activity log show?
  • Can the database actually handle create/read/update/delete?

Usage:
  python agents/db_health_agent.py
  python agents/db_health_agent.py --focus counter   # just check the ID counter
  python agents/db_health_agent.py --focus duplicates
  python agents/db_health_agent.py --focus activity
"""

import os
import sys
import json
import argparse
from datetime import date, datetime

# ── Setup paths ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Anthropic ──────────────────────────────────────────────────────────────────
try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed.")
    print("  Fix: pip install anthropic")
    sys.exit(1)

# ── SQLAlchemy ─────────────────────────────────────────────────────────────────
try:
    from sqlalchemy import create_engine, text
except ImportError:
    print("ERROR: sqlalchemy not installed.")
    sys.exit(1)

# ── Rich for output ────────────────────────────────────────────────────────────
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
        def rule(self, t=""): print(f"\n{'─'*60}\n{t}\n{'─'*60}")
    console = _C()


# ══════════════════════════════════════════════════════════════════════════════
# DATA COLLECTION — pull facts from the database
# ══════════════════════════════════════════════════════════════════════════════

GLOBAL_ID_TABLES = [
    "announcements", "sermons", "podcast_episodes",
    "podcast_series", "gallery_images", "ongoing_events", "papers"
]

def collect_db_snapshot(conn) -> dict:
    """Collect a snapshot of the database state for Claude to analyze."""
    data = {}

    # 1. Table counts
    table_counts = {}
    all_tables = GLOBAL_ID_TABLES + [
        "sermon_series", "teaching_series", "teaching_series_sessions",
        "users", "audit_log", "site_content", "global_id_counter"
    ]
    for t in all_tables:
        try:
            table_counts[t] = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        except Exception:
            table_counts[t] = "MISSING TABLE"
    data["table_counts"] = table_counts

    # 2. GlobalIDCounter
    try:
        counter = conn.execute(
            text("SELECT next_id FROM global_id_counter WHERE id = 1")
        ).scalar()
        data["global_id_counter"] = counter

        max_ids = {}
        for t in GLOBAL_ID_TABLES:
            try:
                max_ids[t] = conn.execute(text(f"SELECT MAX(id) FROM {t}")).scalar() or 0
            except Exception:
                max_ids[t] = "ERROR"
        data["max_ids_per_table"] = max_ids
    except Exception as e:
        data["global_id_counter"] = f"ERROR: {e}"
        data["max_ids_per_table"] = {}

    # 3. Duplicates
    duplicates = {}

    try:
        rows = conn.execute(text("""
            SELECT LOWER(TRIM(title)), COUNT(*), STRING_AGG(id::text, ',')
            FROM announcements GROUP BY LOWER(TRIM(title)) HAVING COUNT(*) > 1 LIMIT 10
        """)).fetchall()
        if rows:
            duplicates["announcements_same_title"] = [
                {"title": r[0], "count": r[1], "ids": r[2]} for r in rows
            ]
    except Exception: pass

    try:
        rows = conn.execute(text("""
            SELECT LOWER(TRIM(title)), date::text, COUNT(*), STRING_AGG(id::text, ',')
            FROM sermons GROUP BY LOWER(TRIM(title)), date HAVING COUNT(*) > 1 LIMIT 10
        """)).fetchall()
        if rows:
            duplicates["sermons_same_title_and_date"] = [
                {"title": r[0], "date": r[1], "count": r[2], "ids": r[3]} for r in rows
            ]
    except Exception: pass

    try:
        rows = conn.execute(text("""
            SELECT original_id, COUNT(*), STRING_AGG(id::text, ',')
            FROM podcast_episodes WHERE original_id IS NOT NULL
            GROUP BY original_id HAVING COUNT(*) > 1 LIMIT 10
        """)).fetchall()
        if rows:
            duplicates["podcast_episodes_same_rss_id"] = [
                {"original_id": r[0], "count": r[1], "ids": r[2]} for r in rows
            ]
    except Exception: pass

    data["duplicates"] = duplicates

    # 4. Orphaned foreign keys
    orphans = {}
    fk_checks = [
        ("sermons_missing_series", "SELECT COUNT(*) FROM sermons s WHERE s.series_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sermon_series p WHERE p.id = s.series_id)"),
        ("sermons_missing_speaker", "SELECT COUNT(*) FROM sermons s WHERE s.speaker_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM users p WHERE p.id = s.speaker_id)"),
        ("podcast_episodes_missing_series", "SELECT COUNT(*) FROM podcast_episodes e WHERE e.series_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM podcast_series p WHERE p.id = e.series_id)"),
        ("teaching_sessions_missing_series", "SELECT COUNT(*) FROM teaching_series_sessions s WHERE NOT EXISTS (SELECT 1 FROM teaching_series p WHERE p.id = s.series_id)"),
    ]
    for name, query in fk_checks:
        try:
            count = conn.execute(text(query)).scalar()
            if count and count > 0:
                orphans[name] = count
        except Exception: pass
    data["orphaned_foreign_keys"] = orphans

    # 5. Stale active content (expired but still active=true)
    today = date.today().isoformat()
    stale = {}
    for t in ["announcements", "sermons", "podcast_episodes", "ongoing_events"]:
        try:
            count = conn.execute(text(
                f"SELECT COUNT(*) FROM {t} WHERE active = true AND expires_at IS NOT NULL AND expires_at < '{today}'"
            )).scalar()
            if count and count > 0:
                stale[t] = count
        except Exception: pass
    data["stale_active_content"] = stale

    # 6. Recent audit log
    try:
        rows = conn.execute(text("""
            SELECT timestamp::text, "user", action, entity_type, entity_id, entity_title
            FROM audit_log ORDER BY timestamp DESC LIMIT 20
        """)).fetchall()
        data["recent_audit_log"] = [
            {"time": r[0], "user": r[1], "action": r[2],
             "type": r[3], "id": r[4], "title": str(r[5] or "")[:60]}
            for r in rows
        ]
    except Exception as e:
        data["recent_audit_log"] = []

    # 7. CRUD smoke test (rolled back — no real changes)
    crud_results = {}
    test_id = 999999
    try:
        with conn.begin_nested():
            conn.execute(text(
                "INSERT INTO announcements (id, title, description, active, type, date_entered, revision) "
                "VALUES (:id, '__AGENT_TEST__', 'Agent smoke test', true, 'announcement', NOW(), 1)"
            ), {"id": test_id})
            found = conn.execute(text("SELECT title FROM announcements WHERE id = :id"), {"id": test_id}).scalar()
            crud_results["create_and_read"] = "OK" if found == "__AGENT_TEST__" else "FAILED"
            conn.execute(text("UPDATE announcements SET title = '__AGENT_TEST_UPDATED__' WHERE id = :id"), {"id": test_id})
            updated = conn.execute(text("SELECT title FROM announcements WHERE id = :id"), {"id": test_id}).scalar()
            crud_results["update"] = "OK" if updated == "__AGENT_TEST_UPDATED__" else "FAILED"
            conn.execute(text("DELETE FROM announcements WHERE id = :id"), {"id": test_id})
            gone = conn.execute(text("SELECT COUNT(*) FROM announcements WHERE id = :id"), {"id": test_id}).scalar()
            crud_results["delete"] = "OK" if gone == 0 else "FAILED"
            raise Exception("rollback")
    except Exception as e:
        if "rollback" not in str(e):
            crud_results = {"error": str(e)}
    data["crud_smoke_test"] = crud_results

    # 8. Schema info (column names for key tables)
    schema_info = {}
    try:
        for t in ["announcements", "sermons", "global_id_counter"]:
            rows = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = :t ORDER BY ordinal_position"
            ), {"t": t}).fetchall()
            schema_info[t] = [r[0] for r in rows]
    except Exception: pass
    data["schema_columns"] = schema_info

    # 9. Recent content (a few records from each main table)
    recent = {}
    try:
        rows = conn.execute(text(
            "SELECT id, title, type, active, date_entered::text FROM announcements ORDER BY date_entered DESC LIMIT 5"
        )).fetchall()
        recent["announcements"] = [{"id": r[0], "title": r[1], "type": r[2], "active": r[3], "entered": r[4]} for r in rows]
    except Exception: pass
    try:
        rows = conn.execute(text(
            "SELECT id, title, date::text, active FROM sermons ORDER BY date DESC LIMIT 5"
        )).fetchall()
        recent["sermons"] = [{"id": r[0], "title": r[1], "date": r[2], "active": r[3]} for r in rows]
    except Exception: pass
    data["recent_records"] = recent

    return data


# ══════════════════════════════════════════════════════════════════════════════
# CLAUDE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a database health expert reviewing the CPC New Haven church website database.

KEY FACTS ABOUT THIS SYSTEM:
- Built on Flask + PostgreSQL hosted on Render
- A collaborator named Chris sometimes edits the database DIRECTLY using a GUI tool called BeaverDB (similar to TablePlus)
- The biggest risk from Chris's direct edits: the GlobalIDCounter can fall behind, causing duplicate primary key errors when content is next saved through the admin panel
- There is a GlobalIDCounter table (one row) that tracks the next ID to use for announcements, sermons, podcasts, gallery images, ongoing events, and papers
- If the counter's `next_id` value is LESS THAN OR EQUAL TO the maximum ID found in any of those tables, it will crash on next content save

YOUR JOB:
- Review the database snapshot provided and give a clear, plain-English health report
- Be direct about what's wrong and what's fine
- Explain things in a way a non-technical person can understand
- Prioritize by severity: critical issues first, then warnings, then good news
- For each issue, explain WHAT it means and HOW TO FIX IT
- Keep it concise — the user can see the raw data, so focus on interpretation and advice

FORMAT:
Use clear sections with emoji:
🔴 CRITICAL — must fix now
🟡 WARNING — should look at soon
✅ ALL GOOD — things that are working
📋 ACTIVITY SUMMARY — what's been happening
💡 RECOMMENDATIONS — things to consider doing

Don't pad with filler text. Be helpful and specific."""


def ask_claude(snapshot: dict, focus: str = None) -> str:
    """Send the DB snapshot to Claude and get a health report."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "ERROR: ANTHROPIC_API_KEY is not set. Add it to your .env file."

    client = anthropic.Anthropic(api_key=api_key)

    focus_instruction = ""
    if focus == "counter":
        focus_instruction = "\n\nFOCUS: The user specifically wants to know about the GlobalIDCounter. Lead with that analysis."
    elif focus == "duplicates":
        focus_instruction = "\n\nFOCUS: The user specifically wants to know about duplicate records. Lead with that analysis."
    elif focus == "activity":
        focus_instruction = "\n\nFOCUS: The user specifically wants to understand the recent activity log. Lead with a summary of who has been doing what."

    user_message = f"""Here is a snapshot of the CPC church website database. Please analyze it and give a health report.

DATABASE SNAPSHOT:
{json.dumps(snapshot, indent=2, default=str)}
{focus_instruction}
"""

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        # Get the text response (skip thinking blocks)
        for block in response.content:
            if block.type == "text":
                return block.text
        return "No response received."
    except anthropic.AuthenticationError:
        return "ERROR: Invalid ANTHROPIC_API_KEY. Check your .env file."
    except anthropic.RateLimitError:
        return "ERROR: Rate limit hit. Try again in a moment."
    except Exception as e:
        return f"ERROR calling Claude: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def get_db_engine():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    try:
        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 10})
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        print(f"ERROR: Cannot connect to database: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Claude-powered database health agent")
    parser.add_argument("--focus", choices=["counter", "duplicates", "activity"],
                        help="Focus Claude's analysis on a specific area")
    args = parser.parse_args()

    if RICH:
        console.print(Panel(
            "[bold white]CPC Database Health Agent[/bold white]\n"
            "[dim]Powered by Claude AI · Collecting data from Render...[/dim]",
            border_style="blue"
        ))
    else:
        print("\n" + "="*60 + "\nCPC DATABASE HEALTH AGENT (Claude AI)\n" + "="*60)

    # Step 1: Connect and collect data
    engine = get_db_engine()
    console.print("  [green]✓ Connected to database[/green]")

    with engine.connect() as conn:
        console.print("  [dim]Collecting database snapshot...[/dim]")
        snapshot = collect_db_snapshot(conn)

    console.print("  [dim]Sending to Claude for analysis...[/dim]\n")

    # Step 2: Ask Claude
    report = ask_claude(snapshot, focus=args.focus)

    # Step 3: Display report
    if RICH:
        console.rule("[bold cyan]Claude's Report[/bold cyan]")
        console.print(Markdown(report))
    else:
        print("\n" + "="*60 + "\nCLAUDE'S REPORT\n" + "="*60)
        print(report)

    console.print("\n[dim]Run with --focus counter|duplicates|activity for a focused report[/dim]")


if __name__ == "__main__":
    main()
