#!/usr/bin/env bash
# One command to sync local DB from live. Uses LIVE_DATABASE_URL from .env.
# Usage: ./sync_from_live.sh   (or: bash sync_from_live.sh)
# Sermon/SermonSeries are managed by Chris on Render — skipped by default to avoid overwriting.
# To sync everything: python sync_db.py (without --skip)
set -e
cd "$(dirname "$0")"
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
if [ -z "$LIVE_DATABASE_URL" ]; then
  echo "LIVE_DATABASE_URL is not set. Add it to .env, or run:"
  echo "  LIVE_DATABASE_URL='postgresql://user:pass@host/db' python sync_db.py"
  exit 1
fi
python sync_db.py --skip Sermon,SermonSeries "$@"
