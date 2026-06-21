#!/bin/bash
# Start automatic podcast updates
# This script runs the podcast scheduler in the background

echo "🎙️  Starting CPC New Haven Podcast Updates..."
echo "This will automatically fetch new episodes every 6 hours"
echo "Press Ctrl+C to stop"

cd "$(dirname "$0")"
python podcast_scheduler.py
