#!/usr/bin/env python3
"""
db_agent.py  —  CPC Database Health Agent
==========================================
Run this any time to check the Render PostgreSQL database for health issues,
especially useful after Chris makes direct changes via BeaverDB.

What it checks:
  1. Can we connect to the database?
  2. How many records are in each table?
  3. Is the GlobalIDCounter ahead of all content IDs? (critical for Chris's edits)
  4. Are there duplicate records?
  5. Are there broken links (orphaned foreign keys)?
  6. Is expired content still showing as active?
  7. What's the recent activity history?
  8. Can we actually Create, Read, Update, Delete? (CRUD smoke test)

Usage:
  python db_agent.py              # Full health report
  python db_agent.py --quick      # Counts + critical checks only
  python db_agent.py --history    # Just the recent audit log
  python db_agent.py --dupes      # Just duplicate detection
  python db_agent.py --fix-counter  # Fix GlobalIDCounter if it's out of sync
"""

import sys
import os
import argparse
from datetime import datetime, date, timedelta

# ── Load .env so DATABASE_URL is available ─────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # If dotenv not installed, rely on environment variables

# ── Rich for pretty output ─────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    from rich.text import Text
    console = Console()
    RICH = True
except ImportError:
    RICH = False
    class _FallbackConsole:
        def print(self, *args, **kwargs): print(*args)
        def rule(self, title=""): print(f"\n{'='*60}\n{title}\n{'='*60}")
    console = _FallbackConsole()

# ── SQLAlchemy ─────────────────────────────────────────────────────────────────
try:
    import sqlalchemy as sa
    from sqlalchemy import create_engine, text, inspect
except ImportError:
    console.print("[bold red]ERROR:[/bold red] SQLAlchemy not installed.")
    console.print("  Fix: pip install sqlalchemy psycopg2-binary")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────────────────────
# SECTION 1 — DATABASE CONNECTION
# ──────────────────────────────────────────────────────────────────────────────

def get_engine():
    """Connect to the database using DATABASE_URL from .env"""
    url = os.getenv("DATABASE_URL", "")
    if not url:
        console.print("[bold red]ERROR:[/bold red] DATABASE_URL is not set.")
        console.print("  Make sure your .env file has:  DATABASE_URL=postgresql://...")
        sys.exit(1)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    try:
        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        console.print(f"[bold red]CANNOT CONNECT TO DATABASE:[/bold red] {e}")
        console.print("\nCheck that:")
        console.print("  • Your .env has the correct DATABASE_URL")
        console.print("  • Your Render database is running (not sleeping)")
        console.print("  • You are connected to the internet")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 2 — TABLE COUNTS
# ──────────────────────────────────────────────────────────────────────────────

# Tables that use GlobalIDCounter for their primary key
GLOBAL_ID_TABLES = [
    "announcements",
    "sermons",
    "podcast_episodes",
    "podcast_series",
    "gallery_images",
    "ongoing_events",
    "papers",
]

# All content tables
ALL_CONTENT_TABLES = GLOBAL_ID_TABLES + [
    "sermon_series",
    "teaching_series",
    "teaching_series_sessions",
    "users",
    "audit_log",
    "site_content",
    "bible_books",
    "bible_chapters",
    "global_id_counter",
]


def check_table_counts(conn):
    """Return row counts for all tables."""
    results = {}
    for table in ALL_CONTENT_TABLES:
        try:
            row = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            results[table] = row
        except Exception:
            results[table] = "TABLE MISSING"
    return results


def print_table_counts(counts):
    if RICH:
        t = Table(title="Table Row Counts", box=box.ROUNDED, show_header=True)
        t.add_column("Table", style="cyan")
        t.add_column("Rows", justify="right", style="green")
        t.add_column("Status", style="yellow")
        for table, count in counts.items():
            if count == "TABLE MISSING":
                t.add_row(table, "—", "[bold red]MISSING[/bold red]")
            elif count == 0:
                t.add_row(table, "0", "[dim]empty[/dim]")
            else:
                t.add_row(table, str(count), "")
        console.print(t)
    else:
        print("\n=== TABLE COUNTS ===")
        for table, count in counts.items():
            print(f"  {table:<35} {count}")


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 3 — GLOBALIDCOUNTER CHECK (most important for Chris's direct edits)
# ──────────────────────────────────────────────────────────────────────────────

def check_global_id_counter(conn):
    """
    The GlobalIDCounter tracks the next ID to use for content records.
    If Chris adds records directly via BeaverDB with high IDs, the counter
    could be behind — causing duplicate key errors when the app tries to add
    new content.
    """
    issues = []
    warnings_list = []

    # Get current counter value
    try:
        counter_val = conn.execute(
            text("SELECT next_id FROM global_id_counter WHERE id = 1")
        ).scalar()
        if counter_val is None:
            issues.append("GlobalIDCounter row is MISSING (id=1 does not exist)")
            return issues, warnings_list, None, {}
    except Exception as e:
        issues.append(f"Cannot read global_id_counter: {e}")
        return issues, warnings_list, None, {}

    # Get max IDs from all tables that use the global counter
    max_ids = {}
    for table in GLOBAL_ID_TABLES:
        try:
            max_id = conn.execute(text(f"SELECT MAX(id) FROM {table}")).scalar() or 0
            max_ids[table] = max_id
        except Exception:
            max_ids[table] = 0

    overall_max = max(max_ids.values()) if max_ids else 0

    if counter_val <= overall_max:
        worst_table = max(max_ids, key=lambda k: max_ids[k])
        issues.append(
            f"GlobalIDCounter ({counter_val}) is BEHIND the highest ID in '{worst_table}' ({max_ids[worst_table]}). "
            f"Next content save will cause a DUPLICATE KEY ERROR. Run with --fix-counter to fix."
        )
    elif counter_val <= overall_max + 5:
        warnings_list.append(
            f"GlobalIDCounter ({counter_val}) is close to the highest existing ID ({overall_max}). "
            f"This is OK but worth knowing."
        )

    # Check for IDs that are >= counter (these were inserted bypassing the counter)
    bypassed = {}
    for table, max_id in max_ids.items():
        if max_id >= counter_val:
            # Find the specific records
            try:
                rows = conn.execute(
                    text(f"SELECT id FROM {table} WHERE id >= :cval ORDER BY id"),
                    {"cval": counter_val}
                ).fetchall()
                bypassed[table] = [r[0] for r in rows]
            except Exception:
                bypassed[table] = [max_id]

    return issues, warnings_list, counter_val, max_ids


def print_counter_check(issues, warnings_list, counter_val, max_ids):
    if RICH:
        console.rule("[bold cyan]GlobalIDCounter Check[/bold cyan]")
    else:
        print("\n=== GLOBALIDCOUNTER CHECK ===")

    if counter_val is not None:
        console.print(f"  Current counter value: [bold]{counter_val}[/bold]")
        if RICH:
            t = Table(box=box.SIMPLE, show_header=True)
            t.add_column("Table", style="cyan")
            t.add_column("Max ID in table", justify="right")
            t.add_column("Gap (counter - max)", justify="right")
            for table, max_id in sorted(max_ids.items(), key=lambda x: -x[1]):
                gap = counter_val - max_id
                color = "green" if gap > 0 else "red"
                t.add_row(table, str(max_id), f"[{color}]+{gap}[/{color}]" if gap > 0 else f"[red]{gap}[/red]")
            console.print(t)

    for issue in issues:
        console.print(f"  [bold red]✗ CRITICAL:[/bold red] {issue}")
    for w in warnings_list:
        console.print(f"  [yellow]⚠ WARNING:[/yellow] {w}")
    if not issues and not warnings_list:
        console.print("  [green]✓ GlobalIDCounter looks healthy.[/green]")


def fix_global_id_counter(conn):
    """Set the GlobalIDCounter to be safe (max across all tables + 10 buffer)."""
    max_ids = {}
    for table in GLOBAL_ID_TABLES:
        try:
            max_id = conn.execute(text(f"SELECT MAX(id) FROM {table}")).scalar() or 0
            max_ids[table] = max_id
        except Exception:
            max_ids[table] = 0

    overall_max = max(max_ids.values()) if max_ids else 0
    new_value = overall_max + 10  # buffer of 10 so we don't immediately hit another conflict

    console.print(f"\n[yellow]Current max ID across all tables: {overall_max}[/yellow]")
    console.print(f"[yellow]Will set GlobalIDCounter to: {new_value}[/yellow]")

    confirm = input("\nType 'yes' to apply this fix: ").strip().lower()
    if confirm != "yes":
        console.print("[dim]Cancelled.[/dim]")
        return

    conn.execute(
        text("UPDATE global_id_counter SET next_id = :new_val WHERE id = 1"),
        {"new_val": new_value}
    )
    conn.commit()
    console.print(f"[bold green]✓ GlobalIDCounter updated to {new_value}.[/bold green]")


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 4 — DUPLICATE DETECTION
# ──────────────────────────────────────────────────────────────────────────────

def find_duplicates(conn):
    """Find likely duplicate records in key tables."""
    duplicates = {}

    # Announcements: same title (case-insensitive)
    try:
        rows = conn.execute(text("""
            SELECT LOWER(TRIM(title)) as norm_title, COUNT(*) as cnt,
                   STRING_AGG(id::text, ', ' ORDER BY id) as ids
            FROM announcements
            GROUP BY LOWER(TRIM(title))
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
            LIMIT 20
        """)).fetchall()
        if rows:
            duplicates["announcements (same title)"] = [
                {"title": r[0], "count": r[1], "ids": r[2]} for r in rows
            ]
    except Exception as e:
        duplicates["announcements_error"] = str(e)

    # Sermons: same title + date
    try:
        rows = conn.execute(text("""
            SELECT LOWER(TRIM(title)) as norm_title, date, COUNT(*) as cnt,
                   STRING_AGG(id::text, ', ' ORDER BY id) as ids
            FROM sermons
            GROUP BY LOWER(TRIM(title)), date
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
            LIMIT 20
        """)).fetchall()
        if rows:
            duplicates["sermons (same title+date)"] = [
                {"title": r[0], "date": str(r[1]), "count": r[2], "ids": r[3]} for r in rows
            ]
    except Exception as e:
        duplicates["sermons_error"] = str(e)

    # Podcast episodes: same title in same series
    try:
        rows = conn.execute(text("""
            SELECT series_id, LOWER(TRIM(title)) as norm_title, COUNT(*) as cnt,
                   STRING_AGG(id::text, ', ' ORDER BY id) as ids
            FROM podcast_episodes
            GROUP BY series_id, LOWER(TRIM(title))
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
            LIMIT 20
        """)).fetchall()
        if rows:
            duplicates["podcast_episodes (same series+title)"] = [
                {"series_id": r[0], "title": r[1], "count": r[2], "ids": r[3]} for r in rows
            ]
    except Exception as e:
        duplicates["podcast_episodes_error"] = str(e)

    # Podcast episodes: same original_id (from RSS import running twice)
    try:
        rows = conn.execute(text("""
            SELECT original_id, COUNT(*) as cnt,
                   STRING_AGG(id::text, ', ' ORDER BY id) as ids
            FROM podcast_episodes
            WHERE original_id IS NOT NULL
            GROUP BY original_id
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
            LIMIT 20
        """)).fetchall()
        if rows:
            duplicates["podcast_episodes (same original_id / RSS duplicate)"] = [
                {"original_id": r[0], "count": r[1], "ids": r[2]} for r in rows
            ]
    except Exception as e:
        pass

    # Sermons: same episode_number within same series
    try:
        rows = conn.execute(text("""
            SELECT series_id, episode_number, COUNT(*) as cnt,
                   STRING_AGG(title, ' / ' ORDER BY id) as titles
            FROM sermons
            WHERE series_id IS NOT NULL AND episode_number IS NOT NULL
            GROUP BY series_id, episode_number
            HAVING COUNT(*) > 1
            LIMIT 20
        """)).fetchall()
        if rows:
            duplicates["sermons (duplicate episode numbers in same series)"] = [
                {"series_id": r[0], "episode_number": r[1], "count": r[2], "titles": r[3]} for r in rows
            ]
    except Exception:
        pass

    return duplicates


def print_duplicates(duplicates):
    if RICH:
        console.rule("[bold cyan]Duplicate Detection[/bold cyan]")
    else:
        print("\n=== DUPLICATE DETECTION ===")

    if not duplicates:
        console.print("  [green]✓ No duplicates found.[/green]")
        return

    for category, items in duplicates.items():
        if isinstance(items, str):
            console.print(f"  [red]Error checking {category}: {items}[/red]")
            continue
        console.print(f"\n  [bold yellow]⚠ {category}[/bold yellow] — {len(items)} duplicate group(s):")
        for item in items[:10]:  # Limit to 10 per category
            if RICH:
                parts = [f"[cyan]{k}[/cyan]=[white]{v}[/white]" for k, v in item.items()]
                console.print(f"    • {', '.join(parts)}")
            else:
                print(f"    • {item}")


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 5 — ORPHANED FOREIGN KEYS
# ──────────────────────────────────────────────────────────────────────────────

def check_orphaned_fks(conn):
    """Check for records that reference non-existent parent records."""
    issues = []

    checks = [
        # (description, child_table, child_col, parent_table)
        ("Sermons → sermon_series", "sermons", "series_id", "sermon_series"),
        ("Sermons → users (speaker)", "sermons", "speaker_id", "users"),
        ("Sermons → bible_books", "sermons", "bible_book_id", "bible_books"),
        ("Podcast episodes → podcast_series", "podcast_episodes", "series_id", "podcast_series"),
        ("Teaching sessions → teaching_series", "teaching_series_sessions", "series_id", "teaching_series"),
    ]

    for desc, child_table, child_col, parent_table in checks:
        try:
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM {child_table} c
                WHERE c.{child_col} IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM {parent_table} p WHERE p.id = c.{child_col}
                  )
            """)).scalar()
            if count and count > 0:
                issues.append({
                    "description": desc,
                    "count": count,
                    "details": f"{count} records in '{child_table}' have a '{child_col}' pointing to a non-existent '{parent_table}' record"
                })
        except Exception as e:
            issues.append({"description": desc, "count": "?", "details": f"Error: {e}"})

    return issues


def print_fk_check(issues):
    if RICH:
        console.rule("[bold cyan]Orphaned Foreign Key Check[/bold cyan]")
    else:
        print("\n=== ORPHANED FOREIGN KEY CHECK ===")

    if not issues:
        console.print("  [green]✓ No orphaned foreign keys found.[/green]")
        return

    for issue in issues:
        console.print(f"  [bold red]✗[/bold red] {issue['description']}: {issue['details']}")


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 6 — STALE ACTIVE CONTENT (expired but still showing)
# ──────────────────────────────────────────────────────────────────────────────

def check_stale_content(conn):
    """Find content that has an expired date but is still marked active=True."""
    today = date.today().isoformat()
    stale = {}

    tables_with_expiry = [
        ("announcements", "title"),
        ("sermons", "title"),
        ("podcast_episodes", "title"),
        ("ongoing_events", "title"),
        ("gallery_images", "name"),
    ]

    for table, title_col in tables_with_expiry:
        try:
            rows = conn.execute(text(f"""
                SELECT id, {title_col}, expires_at
                FROM {table}
                WHERE active = true
                  AND expires_at IS NOT NULL
                  AND expires_at < :today
                ORDER BY expires_at ASC
                LIMIT 10
            """), {"today": today}).fetchall()
            if rows:
                stale[table] = [{"id": r[0], "title": r[1], "expires_at": str(r[2])} for r in rows]
        except Exception:
            pass

    return stale


def print_stale_content(stale):
    if RICH:
        console.rule("[bold cyan]Stale Active Content (expired but still showing)[/bold cyan]")
    else:
        print("\n=== STALE ACTIVE CONTENT ===")

    if not stale:
        console.print("  [green]✓ No stale active content found.[/green]")
        return

    for table, items in stale.items():
        console.print(f"\n  [yellow]⚠ {table}[/yellow] — {len(items)} expired item(s) still active:")
        for item in items:
            console.print(f"    • ID {item['id']}: \"{item['title']}\" expired {item['expires_at']}")


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 7 — RECENT ACTIVITY HISTORY
# ──────────────────────────────────────────────────────────────────────────────

def get_recent_activity(conn, limit=30):
    """Pull recent entries from the audit_log table."""
    try:
        rows = conn.execute(text("""
            SELECT timestamp, user, action, entity_type, entity_id, entity_title, details
            FROM audit_log
            ORDER BY timestamp DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()
        return rows
    except Exception as e:
        return []


def print_activity_history(rows, limit=30):
    if RICH:
        console.rule(f"[bold cyan]Recent Activity Log (last {limit})[/bold cyan]")
    else:
        print(f"\n=== RECENT ACTIVITY LOG (last {limit}) ===")

    if not rows:
        console.print("  [dim]No activity logged yet (audit_log is empty).[/dim]")
        return

    if RICH:
        t = Table(box=box.SIMPLE, show_header=True)
        t.add_column("When", style="dim", min_width=19)
        t.add_column("Who", style="cyan", min_width=10)
        t.add_column("Action", style="yellow", min_width=8)
        t.add_column("Type", style="magenta", min_width=14)
        t.add_column("ID", justify="right", min_width=4)
        t.add_column("Title", style="white", no_wrap=False, min_width=30)
        for r in rows:
            ts = r[0].strftime("%Y-%m-%d %H:%M") if hasattr(r[0], 'strftime') else str(r[0])
            action_color = {"created": "green", "edited": "yellow", "deleted": "red"}.get(str(r[2]), "white")
            t.add_row(
                ts, str(r[1]),
                f"[{action_color}]{r[2]}[/{action_color}]",
                str(r[3]), str(r[4] or ""),
                str(r[5] or "")[:60]
            )
        console.print(t)
    else:
        for r in rows:
            print(f"  {r[0]}  {r[1]:<12}  {r[2]:<8}  {r[3]:<16}  #{r[4]}  {(r[5] or '')[:40]}")


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 8 — CRUD SMOKE TEST
# ──────────────────────────────────────────────────────────────────────────────

def crud_smoke_test(conn):
    """
    Verify that Create, Read, Update, Delete all work.
    Uses a clearly-labelled test record that gets cleaned up immediately.
    """
    results = {}
    test_title = f"__DB_AGENT_TEST_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}__"

    # CREATE — insert a test announcement
    try:
        # Get a safe ID (counter - 1000 could collide, so just use a big temp value)
        # We'll use a transaction and roll it back so no permanent changes
        with conn.begin_nested():
            # Get current counter
            next_id = conn.execute(
                text("SELECT next_id FROM global_id_counter WHERE id = 1")
            ).scalar()
            test_id = (next_id or 9999) + 50000  # Very high temp ID, won't conflict

            conn.execute(text("""
                INSERT INTO announcements (id, title, description, active, type, date_entered, revision)
                VALUES (:id, :title, 'Test record from db_agent.py — safe to delete', true, 'announcement', NOW(), 1)
            """), {"id": test_id, "title": test_title})

            # READ — find the record we just inserted
            row = conn.execute(
                text("SELECT id, title FROM announcements WHERE id = :id"),
                {"id": test_id}
            ).fetchone()

            if row and row[1] == test_title:
                results["CREATE + READ"] = ("ok", f"Inserted and read back record id={test_id}")
            else:
                results["CREATE + READ"] = ("fail", "Inserted but could not read back")

            # UPDATE
            conn.execute(
                text("UPDATE announcements SET title = :new_title WHERE id = :id"),
                {"new_title": test_title + "_UPDATED", "id": test_id}
            )
            updated = conn.execute(
                text("SELECT title FROM announcements WHERE id = :id"),
                {"id": test_id}
            ).scalar()
            if updated and "_UPDATED" in updated:
                results["UPDATE"] = ("ok", "Update succeeded")
            else:
                results["UPDATE"] = ("fail", "Update did not change the record")

            # DELETE
            conn.execute(
                text("DELETE FROM announcements WHERE id = :id"),
                {"id": test_id}
            )
            gone = conn.execute(
                text("SELECT COUNT(*) FROM announcements WHERE id = :id"),
                {"id": test_id}
            ).scalar()
            if gone == 0:
                results["DELETE"] = ("ok", "Delete succeeded, no trace left")
            else:
                results["DELETE"] = ("fail", "Delete did not remove the record")

            # Roll back everything — no actual changes saved
            raise Exception("rollback_on_purpose")

    except Exception as e:
        if "rollback_on_purpose" not in str(e):
            for op in ["CREATE + READ", "UPDATE", "DELETE"]:
                if op not in results:
                    results[op] = ("fail", str(e))

    return results


def print_crud_results(results):
    if RICH:
        console.rule("[bold cyan]CRUD Smoke Test[/bold cyan]")
    else:
        print("\n=== CRUD SMOKE TEST ===")

    console.print("  [dim](Test records are created inside a rolled-back transaction — no real data changed)[/dim]\n")

    if not results:
        console.print("  [red]CRUD test could not run.[/red]")
        return

    for op, (status, detail) in results.items():
        icon = "[green]✓[/green]" if status == "ok" else "[red]✗[/red]"
        label = f"[green]{op}[/green]" if status == "ok" else f"[red]{op}[/red]"
        console.print(f"  {icon} {label}: {detail}")


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 9 — SCHEMA CHECK (make sure all expected columns exist)
# ──────────────────────────────────────────────────────────────────────────────

EXPECTED_COLUMNS = {
    "announcements": ["id", "title", "description", "active", "type", "expires_at", "revision", "updated_at", "updated_by", "show_in_banner", "image_display_type", "event_start_time", "event_end_time"],
    "sermons": ["id", "title", "speaker", "speaker_id", "scripture", "date", "active", "series_id", "episode_number", "bible_book_id", "expires_at"],
    "podcast_episodes": ["id", "series_id", "number", "title", "source", "original_id", "expires_at"],
    "global_id_counter": ["id", "next_id"],
    "audit_log": ["id", "timestamp", "user", "action", "entity_type", "entity_id", "entity_title", "details"],
}


def check_schema(conn):
    """Verify expected columns exist in key tables."""
    missing = {}
    insp = inspect(conn)
    for table, expected_cols in EXPECTED_COLUMNS.items():
        try:
            existing_cols = {c["name"] for c in insp.get_columns(table)}
            missing_cols = [c for c in expected_cols if c not in existing_cols]
            if missing_cols:
                missing[table] = missing_cols
        except Exception as e:
            missing[table] = [f"TABLE ERROR: {e}"]
    return missing


def print_schema_check(missing):
    if RICH:
        console.rule("[bold cyan]Schema Check[/bold cyan]")
    else:
        print("\n=== SCHEMA CHECK ===")

    if not missing:
        console.print("  [green]✓ All expected columns are present.[/green]")
        return

    for table, cols in missing.items():
        console.print(f"  [bold red]✗ {table}[/bold red] — missing columns: {', '.join(cols)}")
        console.print(f"    → Run: flask db migrate && flask db upgrade")


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 10 — SUMMARY BANNER
# ──────────────────────────────────────────────────────────────────────────────

def print_summary(counter_issues, duplicates, fk_issues, stale, schema_missing, crud_results):
    all_ok = (
        len(counter_issues) == 0
        and len(duplicates) == 0
        and len(fk_issues) == 0
        and len(stale) == 0
        and len(schema_missing) == 0
        and all(v[0] == "ok" for v in crud_results.values())
    )

    if RICH:
        console.rule()
        if all_ok:
            console.print(Panel(
                "[bold green]ALL CHECKS PASSED[/bold green]\n"
                "Database is healthy. No issues found.",
                title="SUMMARY", border_style="green"
            ))
        else:
            lines = []
            if counter_issues:
                lines.append(f"[red]• {len(counter_issues)} GlobalIDCounter issue(s) — CRITICAL[/red]")
            if duplicates:
                lines.append(f"[yellow]• Duplicates found in: {', '.join(duplicates.keys())}[/yellow]")
            if fk_issues:
                lines.append(f"[yellow]• {len(fk_issues)} orphaned foreign key issue(s)[/yellow]")
            if stale:
                lines.append(f"[yellow]• Stale active content in: {', '.join(stale.keys())}[/yellow]")
            if schema_missing:
                lines.append(f"[red]• Schema missing columns in: {', '.join(schema_missing.keys())}[/red]")
            failed_crud = [op for op, (s, _) in crud_results.items() if s != "ok"]
            if failed_crud:
                lines.append(f"[red]• CRUD failures: {', '.join(failed_crud)}[/red]")
            console.print(Panel(
                "\n".join(lines),
                title="[bold yellow]ISSUES FOUND[/bold yellow]",
                border_style="yellow"
            ))
    else:
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        if all_ok:
            print("ALL CHECKS PASSED — Database is healthy.")
        else:
            print("ISSUES FOUND:")
            if counter_issues:
                print(f"  CRITICAL: GlobalIDCounter out of sync ({len(counter_issues)} issue(s))")
            if duplicates:
                print(f"  WARNING: Duplicates in: {', '.join(duplicates.keys())}")
            if fk_issues:
                print(f"  WARNING: {len(fk_issues)} orphaned FK issue(s)")
            if stale:
                print(f"  WARNING: Stale content in: {', '.join(stale.keys())}")
            if schema_missing:
                print(f"  ERROR: Missing columns in: {', '.join(schema_missing.keys())}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CPC Database Health Agent")
    parser.add_argument("--quick", action="store_true", help="Only counts + critical checks")
    parser.add_argument("--history", action="store_true", help="Only recent audit log")
    parser.add_argument("--dupes", action="store_true", help="Only duplicate detection")
    parser.add_argument("--fix-counter", action="store_true", help="Fix GlobalIDCounter if out of sync")
    parser.add_argument("--history-limit", type=int, default=30, help="How many audit log rows to show (default: 30)")
    args = parser.parse_args()

    if RICH:
        console.print(Panel(
            "[bold white]CPC Web App — Database Health Agent[/bold white]\n"
            "[dim]Checking Render PostgreSQL...[/dim]",
            border_style="blue"
        ))
    else:
        print("\n" + "=" * 60)
        print("CPC WEB APP — DATABASE HEALTH AGENT")
        print("=" * 60)

    # Connect
    engine = get_engine()
    console.print(f"  [green]✓ Connected to database[/green]\n")

    with engine.connect() as conn:
        # --fix-counter mode
        if args.fix_counter:
            fix_global_id_counter(conn)
            return

        # --history mode
        if args.history:
            rows = get_recent_activity(conn, limit=args.history_limit)
            print_activity_history(rows, limit=args.history_limit)
            return

        # --dupes mode
        if args.dupes:
            dupes = find_duplicates(conn)
            print_duplicates(dupes)
            return

        # Full or quick report
        counts = check_table_counts(conn)
        print_table_counts(counts)

        counter_issues, counter_warnings, counter_val, max_ids = check_global_id_counter(conn)
        print_counter_check(counter_issues, counter_warnings, counter_val, max_ids)

        schema_missing = check_schema(conn)
        print_schema_check(schema_missing)

        if not args.quick:
            dupes = find_duplicates(conn)
            print_duplicates(dupes)

            fk_issues = check_orphaned_fks(conn)
            print_fk_check(fk_issues)

            stale = check_stale_content(conn)
            print_stale_content(stale)

            crud_results = crud_smoke_test(conn)
            print_crud_results(crud_results)

            rows = get_recent_activity(conn, limit=args.history_limit)
            print_activity_history(rows, limit=args.history_limit)
        else:
            dupes, fk_issues, stale, crud_results = {}, [], {}, {"skipped": ("ok", "use full report")}

        print_summary(counter_issues, dupes, fk_issues, stale, schema_missing, crud_results)

        console.print("\n[dim]Tip: Run with --fix-counter if GlobalIDCounter is out of sync[/dim]")
        console.print("[dim]Tip: Run with --history to see just the activity log[/dim]")
        console.print("[dim]Tip: Run with --dupes to focus on duplicate detection[/dim]\n")


if __name__ == "__main__":
    main()
