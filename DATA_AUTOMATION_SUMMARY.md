# Data Automation Summary

This document outlines which parts of the CPC New Haven website data are automatically fetched and which require manual input.

## 🔄 Automatic Data Sources

These data sources are automatically fetched from external APIs/services:

### 1. **Podcasts/Sermons** (`podcast_fetcher.py`)
- **Source**: RSS feeds from podcast platforms (Spotify, Apple Podcasts, etc.)
- **Frequency**: Scheduled via `podcast_scheduler.py` and `start_podcast_updates.sh`
- **Data**: 
  - Podcast series
  - Episode metadata
  - Thumbnails
  - Links to platforms
- **Storage**: Database (`podcast_series`, `podcast_episodes` tables) + JSON files

### 2. **Newsletter** (`ingest/newsletter.py`)
- **Source**: RSS feed from newsletter service
- **Frequency**: On-demand via `/api/external-data` endpoint (cached 15 minutes)
- **Data**: Newsletter articles and content
- **Storage**: Cached in memory, not persisted to database

### 3. **Events** (`ingest/events.py`)
- **Source**: External events API
- **Frequency**: On-demand via `/api/external-data` endpoint (cached 15 minutes)
- **Data**: Event listings and details
- **Storage**: Cached in memory, not persisted to database

### 4. **Mailchimp** (`ingest/mailchimp.py`)
- **Source**: Mailchimp API
- **Frequency**: On-demand via `/api/external-data` endpoint (cached 15 minutes)
- **Data**: Mailchimp campaign data
- **Storage**: Cached in memory, not persisted to database

### 5. **YouTube** (`ingest/youtube.py`)
- **Source**: YouTube API
- **Frequency**: On-demand via `/api/external-data` endpoint (cached 15 minutes)
- **Data**: YouTube video metadata
- **Storage**: Cached in memory, not persisted to database

## 📝 Manual Data Sources

These require manual input or JSON file updates:

### 1. **Announcements** (`data/announcements.json`)
- **Source**: Manual JSON file or Admin interface
- **Population**: Run `python populate_announcements.py` to sync JSON → Database
- **Storage**: 
  - JSON file: `data/announcements.json`
  - Database: `announcements` table
- **API**: `/api/announcements` (reads from database)

### 2. **Highlights** (`data/highlights.json`)
- **Source**: Manual JSON file or Admin interface
- **Population**: Run `python populate_highlights.py` to sync JSON → Database
- **Storage**: 
  - JSON file: `data/highlights.json`
  - Database: `announcements` table (shared with announcements)
- **API**: `/api/highlights` (reads from database)

### 3. **Events** (`data/events.json`)
- **Source**: Manual JSON file or Admin interface
- **Storage**: JSON file only
- **API**: `/api/events` (reads from JSON)

### 4. **Gallery Images** (`data/gallery.json`)
- **Source**: Manual JSON file or Admin interface
- **Storage**: Database (`gallery_images` table)
- **API**: `/api/gallery` (reads from database)

### 5. **Sermons** (`data/sermons.json`)
- **Source**: Manual JSON file (legacy) or automatic via podcast fetcher
- **Storage**: Database (`sermons` table) + JSON files
- **API**: `/api/sermons` (reads from database)

## 🔧 Data Population Scripts

### Populate Announcements
```bash
python populate_announcements.py
```
Reads from `data/announcements.json` and syncs to database.

### Populate Highlights
```bash
python populate_highlights.py
```
Reads from `data/highlights.json` and syncs to database.

## 📊 Data Flow

```
External APIs (Podcasts, YouTube, etc.)
    ↓
Ingest Scripts (ingest/*.py)
    ↓
Cache (15 min TTL)
    ↓
API Endpoints (/api/external-data)

JSON Files (announcements.json, highlights.json)
    ↓
Population Scripts (populate_*.py)
    ↓
Database (SQLite)
    ↓
API Endpoints (/api/announcements, /api/highlights)
```

## 🎯 Key Endpoints

- `/api/announcements` - Active announcements from database
- `/api/highlights` - All announcements (for highlights page)
- `/api/external-data` - Aggregated external data (newsletter, events, YouTube, Mailchimp)
- `/api/sermons` - Sermons from database
- `/api/podcasts` - Podcast data from database
- `/api/events` - Events from JSON file
- `/api/gallery` - Gallery images from database

