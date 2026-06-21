#!/bin/bash
# Daily Podcast Update Script
# Run this script daily to keep your podcast data updated

echo "🎙️  Starting daily podcast update..."
cd "$(dirname "$0")"

# Run the master control script
python podcast_master.py full-update

# Check if update was successful
if [ $? -eq 0 ]; then
    echo "✅ Daily update completed successfully"
else
    echo "❌ Daily update failed"
    exit 1
fi

echo "📊 Running analytics..."
python podcast_master.py analytics

echo "🎉 Daily podcast maintenance completed!"
