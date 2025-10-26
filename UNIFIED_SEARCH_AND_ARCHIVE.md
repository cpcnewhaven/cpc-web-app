# Unified Search and Archive System

## Overview
This document describes the new unified search functionality and archive system that has been added to the CPC Web App.

## Features

### 1. Unified Search
- **Location**: `/search`
- **Purpose**: Search across all content types simultaneously
- **Content Types Searched**:
  - Sermons (from `data/sermons.json`)
  - Announcements (from database)
  - Podcast Episodes (from database)
  - Events (from database)
  - Gallery Images (from database)

#### Search Capabilities
- Real-time search as you type
- Filter by content type (all, sermons, podcasts, announcements, events, gallery)
- Pagination support (20 results per page)
- Results sorted by date (most recent first)
- Color-coded result types for easy identification

#### API Endpoint
`GET /api/search?q=<query>&type=<content_type>&page=<page>&per_page=<per_page>`

### 2. Archive System
- **Location**: `/archive`
- **Purpose**: Browse historical and older content
- **Content Types Archived**:
  - Sermons older than 90 days
  - Announcements older than 60 days
  - Podcast Episodes older than 90 days

#### Archive Features
- Filter by content type (all, sermons, podcasts, announcements)
- Filter by year for chronological browsing
- Grouped display by content type
- Visual icons for each content type
- Counts per section

#### API Endpoint
`GET /api/archive?type=<content_type>&year=<year>`

## UI/UX Features

### Search Page
- Modern, glassmorphic design
- Large search input with instant feedback
- Tab-based filtering
- Real-time loading states
- Empty state messaging
- Result cards with:
  - Content type badges
  - Title, author, date, category
  - Description/scripture
  - Direct links to content
  - Hover effects

### Archive Page
- Year filter buttons
- Section grouping by content type
- Item thumbnails (when available)
- Color-coded by content type
- Responsive design

## Navigation Updates
- Added "More" dropdown to main navigation (desktop and mobile)
- Contains links to:
  - Search
  - Archive

## Technical Implementation

### Files Created/Modified

#### New Files
1. `templates/search.html` - Search page template
2. `templates/archive.html` - Archive page template

#### Modified Files
1. `app.py` - Added routes and API endpoints:
   - `/search` route
   - `/archive` route
   - `/api/search` API endpoint
   - `/api/archive` API endpoint
2. `templates/base.html` - Added navigation links to search and archive

### Database Integration
- Searches database tables: `announcements`, `podcast_episodes`, `podcast_series`, `ongoing_events`, `gallery_images`
- Also searches JSON files: `data/sermons.json`

### Search Algorithm
- Case-insensitive substring matching
- Searches across multiple fields per content type:
  - Sermons: title, author, scripture
  - Announcements: title, description
  - Podcasts: title, guest, scripture
  - Events: title, description
  - Gallery: name

### Archive Algorithm
- Filters content older than specified days (90 for sermons/podcasts, 60 for announcements)
- Allows year-based filtering
- Sorts by date descending

## Usage Examples

### Search Functionality:
1. Visit `/search`
2. Type search query (e.g., "Luke", "grace", "worship")
3. Click Search or press Enter
4. Use filter tabs to narrow results
5. Click result items to view content

### Archive Functionality:
1. Visit `/archive`
2. Use filter tabs to view specific content types
3. Use year buttons to filter by year
4. Browse historical content
5. Click items to view

## Future Enhancements
- Full-text search with ranking
- Search result highlighting
- Advanced filters (date ranges, categories)
- Saved searches
- Search analytics
- Export archive content
- More granular date filtering

## Notes
- Search is case-insensitive
- Archive cutoff dates are configurable
- Gallery search only searches by image name
- Podcast search handles nullable fields gracefully
