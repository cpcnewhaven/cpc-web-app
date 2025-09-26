#!/bin/bash
# Weekly Analytics Script
# Run this script weekly to generate detailed analytics

echo "📊 Starting weekly analytics..."
cd "$(dirname "$0")"

# Run analytics
python podcast_master.py analytics

# Create backup
python podcast_master.py backup

echo "📈 Weekly analytics completed!"
