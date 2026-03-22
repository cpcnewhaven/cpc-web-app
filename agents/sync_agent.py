#!/usr/bin/env python3
"""
agents/sync_agent.py  —  Frontend/Backend Sync Agent
=====================================================
Claude reads your Flask routes, templates, and database at the same time,
then tells you if the frontend and backend are out of sync — e.g., if a
template expects a field that doesn't exist in the DB, or an API route
returns data in the wrong shape.

Usage:
  python agents/sync_agent.py
"""

import os
import sys
import json

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
    from sqlalchemy import create_engine, text, inspect
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

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SYSTEM_PROMPT = """You are a senior full-stack developer reviewing the CPC New Haven church website.
The app is built with Flask + PostgreSQL. The frontend uses Alpine.js to fetch data from REST API endpoints.

YOUR JOB:
Analyze the provided code snippets and database schema to find sync issues between:
  1. What the database actually stores (columns, data types)
  2. What the API routes return (JSON shape, field names)
  3. What the frontend templates expect (Alpine.js bindings, field references)

WHAT TO LOOK FOR:
  - Field name mismatches (e.g. template uses `sermon.speakerName` but DB has `speaker`)
  - Missing fields (e.g. template uses `announcement.imageUrl` but DB column is `featured_image`)
  - Type mismatches (e.g. template treats `active` as a string but it's a boolean)
  - API routes that query fields that no longer exist in the DB
  - Templates that reference API endpoints that don't exist
  - Content that's in the DB but never exposed by any API route (dead data)
  - API routes that return data but no template uses it

ALSO CHECK:
  - Does the Render DB schema match the models in models.py? (Chris might have added/removed columns)
  - Are there any expected columns that are missing from the live DB?

CONTEXT: A collaborator named Chris sometimes edits the Render PostgreSQL database directly via BeaverDB.
He might add or remove columns without running Flask migrations. This is a common source of sync issues.

FORMAT your response as:
🔴 SYNC BROKEN — feature will fail for users
🟡 POTENTIAL ISSUE — might work but risky
✅ IN SYNC — this area looks good
📝 NOTES — observations that aren't errors but worth knowing
💡 SUGGESTIONS — low-priority improvements"""


def read_file_safely(path: str, max_chars: int = 8000) -> str:
    """Read a file, truncating if it's very long."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > max_chars:
            return content[:max_chars] + f"\n... [truncated, {len(content)} total chars]"
        return content
    except Exception as e:
        return f"[Could not read file: {e}]"


def collect_codebase_snapshot() -> dict:
    """Collect relevant code snippets from the project."""
    snapshot = {}

    # 1. Models (the source of truth for DB schema)
    snapshot["models_py"] = read_file_safely(os.path.join(PROJECT_ROOT, "models.py"))

    # 2. Key API routes — the first 150 lines of relevant route sections in app.py
    # (We can't send all 4549 lines, so we grab key API sections)
    app_py = os.path.join(PROJECT_ROOT, "app.py")
    try:
        with open(app_py, "r") as f:
            lines = f.readlines()

        # Find and extract API route definitions (lines starting with @app.route('/api/')
        api_sections = []
        i = 0
        while i < len(lines):
            if "@app.route('/api/" in lines[i] or "@app.route(\"/api/" in lines[i]:
                # Grab from this route decorator through ~30 lines
                section = "".join(lines[i:min(i+30, len(lines))])
                api_sections.append(section)
            i += 1

        snapshot["api_routes_summary"] = f"Found {len(api_sections)} API routes. First 20:\n\n" + \
            "\n---\n".join(api_sections[:20])
    except Exception as e:
        snapshot["api_routes_summary"] = f"Could not parse app.py: {e}"

    # 3. Key frontend templates
    templates_dir = os.path.join(PROJECT_ROOT, "templates")
    key_templates = [
        "index.html", "sermons.html", "announcements.html",
        "podcasts.html", "events.html", "gallery.html"
    ]
    snapshot["templates"] = {}
    for tmpl in key_templates:
        path = os.path.join(templates_dir, tmpl)
        if os.path.exists(path):
            # Only grab Alpine.js relevant parts (x-data, x-bind, fetch calls)
            content = read_file_safely(path, max_chars=3000)
            snapshot["templates"][tmpl] = content
        else:
            snapshot["templates"][tmpl] = "[file not found]"

    return snapshot


def collect_live_schema(conn) -> dict:
    """Get the actual column names from the live Render database."""
    schema = {}
    key_tables = [
        "announcements", "sermons", "podcast_episodes", "podcast_series",
        "gallery_images", "ongoing_events", "teaching_series",
        "teaching_series_sessions", "users", "site_content"
    ]
    insp = inspect(conn)
    for table in key_tables:
        try:
            cols = insp.get_columns(table)
            schema[table] = [{"name": c["name"], "type": str(c["type"])} for c in cols]
        except Exception:
            schema[table] = "TABLE NOT FOUND IN LIVE DB"
    return schema


def run_agent():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    if RICH:
        console.print(Panel(
            "[bold white]CPC Frontend/Backend Sync Agent[/bold white]\n"
            "[dim]Reading codebase + live DB to find mismatches...[/dim]",
            border_style="cyan"
        ))

    # Connect to DB
    try:
        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 10})
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        console.print("  [green]✓ Connected to database[/green]")
    except Exception as e:
        console.print(f"  [red]Cannot connect: {e}[/red]")
        sys.exit(1)

    # Collect code snapshot
    console.print("  [dim]Reading codebase...[/dim]")
    code_snapshot = collect_codebase_snapshot()

    # Collect live DB schema
    console.print("  [dim]Reading live database schema...[/dim]")
    with engine.connect() as conn:
        live_schema = collect_live_schema(conn)

    console.print("  [dim]Asking Claude to compare them...[/dim]\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    user_message = f"""Please check if the frontend and backend of the CPC church website are in sync.

MODELS.PY (source of truth for expected schema):
{code_snapshot['models_py']}

LIVE DATABASE SCHEMA (actual columns in Render PostgreSQL):
{json.dumps(live_schema, indent=2)}

API ROUTES (how data is served to the frontend):
{code_snapshot['api_routes_summary']}

KEY FRONTEND TEMPLATES:
{json.dumps({k: v[:1500] for k, v in code_snapshot['templates'].items()}, indent=2)}

Please identify any sync issues between what the models define, what the live DB actually has,
what the API routes expose, and what the templates consume."""

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )

        report = next((b.text for b in response.content if b.type == "text"), "No response.")

        if RICH:
            console.rule("[bold cyan]Sync Report[/bold cyan]")
            console.print(Markdown(report))
        else:
            print("\n" + "="*60 + "\nSYNC REPORT\n" + "="*60)
            print(report)

    except Exception as e:
        console.print(f"[red]Claude error: {e}[/red]")


if __name__ == "__main__":
    run_agent()
