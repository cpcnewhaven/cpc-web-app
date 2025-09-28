# External Data Integration Setup Guide

This guide covers setting up external data sources for your CPC web app, including newsletter feeds, calendar events, YouTube videos, and more.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install Flask-Caching ics
```

### 2. Configure Data Sources
Edit `config.py` and replace the placeholder URLs with your actual data sources:

```python
# --- External data sources ---
NEWSLETTER_FEED_URL = "https://your-newsletter-platform.com/feed"
EVENTS_ICS_URL = "https://calendar.google.com/calendar/ical/your-calendar-id/public/basic.ics"
YOUTUBE_CHANNEL_ID = "UC_your_channel_id_here"
BIBLE_API_KEY = "your_bible_api_key"  # Optional
```

### 3. Restart Your App
```bash
flask run
```

### 4. Test the Integration
- Visit `/data-dashboard` to see all external data sources
- Visit `/newsletter` to see newsletter content
- Visit `/api/external-data` to see raw JSON data

## 📊 Available Data Sources

### Newsletter Integration
**Platforms Supported:** Substack, Beehiiv, Ghost, WordPress, Mailchimp (via RSS)

**Setup:**
1. Find your RSS feed URL (usually `/feed` or `/rss`)
2. Add to `NEWSLETTER_FEED_URL` in config.py
3. Content automatically updates every 15 minutes

**Example URLs:**
- Substack: `https://your-publication.substack.com/feed`
- Beehiiv: `https://your-publication.beehiiv.com/feed`
- WordPress: `https://your-site.com/feed`

### Google Calendar Events
**Setup:**
1. Go to your Google Calendar settings
2. Find "Integrate calendar" section
3. Copy the "Public URL in iCal format"
4. Add to `EVENTS_ICS_URL` in config.py

**Example URL:**
```
https://calendar.google.com/calendar/ical/your-calendar-id@group.calendar.google.com/public/basic.ics
```

### YouTube Channel
**Setup:**
1. Go to your YouTube channel
2. Copy the channel ID from the URL or channel settings
3. Add to `YOUTUBE_CHANNEL_ID` in config.py

**Example Channel ID:**
```
UC_your_channel_id_here
```

### Bible Verse API
**Setup:**
1. Get a free API key from [Bible API](https://bible-api.com/) (optional)
2. Add to `BIBLE_API_KEY` in config.py
3. Currently uses free tier (no key required)

## 🏗️ Architecture

### Data Ingester System
The app uses a modular ingester system for external data:

```
ingest/
├── __init__.py
├── base.py          # Base ingester class
├── newsletter.py    # Newsletter RSS ingester
├── events.py        # Calendar ICS ingester
└── youtube.py       # YouTube RSS ingester
```

### API Endpoints
- `/api/newsletter` - Newsletter content
- `/api/events` - Calendar events
- `/api/youtube` - YouTube videos
- `/api/bible-verse` - Bible verse of the day
- `/api/external-data` - All external data combined

### Caching Strategy
- **Newsletter/Events/YouTube:** 15 minutes
- **Bible Verse:** 1 hour
- **External Data Dashboard:** 15 minutes

## 🎯 Platform-Specific Setup

### Substack Newsletter
1. Go to your Substack publication
2. Add `/feed` to the end of your URL
3. Example: `https://cpcnewhaven.substack.com/feed`

### Beehiiv Newsletter
1. Go to your Beehiiv publication
2. Add `/feed` to the end of your URL
3. Example: `https://cpcnewhaven.beehiiv.com/feed`

### Mailchimp Newsletter
**Option A - RSS Feed:**
1. Enable RSS in your Mailchimp campaign settings
2. Use the generated RSS URL

**Option B - Webhook (Advanced):**
1. Set up webhook endpoint: `/webhooks/mailchimp`
2. Configure Mailchimp to send webhooks on campaign send
3. Add API key to environment variables

### Google Calendar
1. Make your calendar public
2. Go to Calendar Settings → Integrate calendar
3. Copy the "Public URL in iCal format"
4. The URL should end with `.ics`

### YouTube Channel
1. Go to your YouTube channel
2. The channel ID is in the URL: `youtube.com/channel/UC_your_channel_id`
3. Or go to Channel Settings → Advanced settings

## 🔧 Troubleshooting

### Common Issues

**"NEWSLETTER_FEED_URL not configured"**
- Make sure you've replaced the placeholder URL in config.py
- Verify the RSS feed URL is accessible

**"Failed to fetch events"**
- Check that your Google Calendar is public
- Verify the ICS URL is correct
- Make sure the calendar has events

**"Failed to fetch YouTube videos"**
- Verify the channel ID is correct
- Check that the channel has public videos

**CORS Errors**
- All data fetching is done server-side to avoid CORS issues
- If you see CORS errors, check your frontend JavaScript

### Testing Individual Sources

Test each data source individually:
```bash
# Test newsletter
curl http://localhost:5000/api/newsletter

# Test events
curl http://localhost:5000/api/events

# Test YouTube
curl http://localhost:5000/api/youtube

# Test all sources
curl http://localhost:5000/api/external-data
```

## 📈 Monitoring

### Data Dashboard
Visit `/data-dashboard` to see:
- Status of all data sources
- Recent content from each source
- Error messages and troubleshooting info
- Last updated timestamps

### Admin Integration
The external data sources integrate with your existing admin system:
- Content is cached for performance
- Errors are logged for debugging
- Data can be exported via existing admin tools

## 🚀 Next Steps

### Additional Integrations
You can easily add more data sources by:
1. Creating a new ingester class in `ingest/`
2. Adding configuration to `config.py`
3. Adding API endpoint to `app.py`
4. Updating the dashboard template

### Suggested Additions
- **Weather API** for service cancellations
- **Planning Center Online** for events and people
- **Tithe.ly/Stripe** for giving data
- **Eventbrite** for event management
- **Social Media** feeds (Twitter, Instagram)

### Performance Optimization
- Consider adding Redis for production caching
- Implement data snapshots for offline fallback
- Add monitoring and alerting for data source failures
- Set up automated testing for data source health

## 📞 Support

If you need help setting up specific platforms or have questions about the integration, check:
1. The data dashboard at `/data-dashboard`
2. Individual API endpoints for error details
3. Server logs for detailed error information

The system is designed to be resilient - if one data source fails, others continue working normally.
