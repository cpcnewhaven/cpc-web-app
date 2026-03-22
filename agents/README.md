# CPC Web App — Claude AI Agents

These agents use Claude AI to analyze your database and codebase
and give you plain-English reports.

## Setup (one-time)

Add your Anthropic API key to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```
Get one at: https://console.anthropic.com

Install the package:
```bash
pip install anthropic
```

---

## Agents

### 1. db_health_agent.py — Database Health Report
```bash
python agents/db_health_agent.py               # Full health report
python agents/db_health_agent.py --focus counter     # Just the ID counter
python agents/db_health_agent.py --focus duplicates  # Just duplicates
python agents/db_health_agent.py --focus activity    # Just recent activity
```
**Run this:** After Chris makes changes via BeaverDB, or when something seems off.

---

### 2. conflict_detector.py — Chris's Edit Conflict Check
```bash
python agents/conflict_detector.py
```
**Run this:** Right after Chris tells you he made changes in BeaverDB.
Claude will check specifically for the kinds of problems that direct DB edits cause.

---

### 3. sync_agent.py — Frontend/Backend Sync Check
```bash
python agents/sync_agent.py
```
**Run this:** When a page isn't showing data correctly, or after adding new features.
Claude reads the code + live database and tells you if they're mismatched.
