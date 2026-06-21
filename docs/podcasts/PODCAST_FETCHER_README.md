# Podcast Fetcher

Automatically pull podcast data from Spotify and Anchor.fm to keep your sermon data up-to-date without manual work.

## Features

- **Spotify Integration**: Fetch episodes from Spotify shows using the Web API
- **Anchor.fm Integration**: Pull episodes from Anchor.fm RSS feeds
- **Automatic Updates**: Schedule regular updates to keep data fresh
- **Smart Merging**: Avoid duplicates and update existing entries
- **Flexible Configuration**: Easy setup for multiple podcasts
- **Error Handling**: Robust error handling and logging

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Setup

```bash
python setup_podcast_fetcher.py
```

This interactive script will help you:
- Configure Spotify API credentials
- Set up Anchor.fm RSS feeds
- Test your configuration
- Set update intervals

### 3. Test the Fetcher

```bash
python podcast_fetcher.py
```

### 4. Start Automatic Updates

```bash
python podcast_scheduler.py
```

## Configuration

The system uses `podcast_config.json` for configuration:

```json
{
  "spotify": {
    "enabled": true,
    "client_id": "your_spotify_client_id",
    "client_secret": "your_spotify_client_secret",
    "show_ids": ["4rOoJ6Egrf8K2IrywzwOMk"]
  },
  "anchor": {
    "enabled": true,
    "rss_urls": ["https://anchor.fm/s/your-podcast/podcast/rss"]
  },
  "settings": {
    "update_interval_hours": 6,
    "backup_before_update": true,
    "log_level": "INFO"
  }
}
```

## Getting API Credentials

### Spotify Web API

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy the Client ID and Client Secret
4. Add your podcast's Spotify Show ID(s)

### Anchor.fm RSS

1. Find your podcast on Anchor.fm
2. The RSS URL is usually: `https://anchor.fm/s/{podcast-name}/podcast/rss`
3. Test the RSS URL in your browser to make sure it works

## Usage

### Manual Fetch

```bash
python podcast_fetcher.py
```

### Scheduled Updates

```bash
# Run continuously with scheduling
python podcast_scheduler.py

# Run once and exit
python podcast_scheduler.py --once
```

### Custom Configuration

```bash
python podcast_scheduler.py --config my_config.json
```

## Data Format

The fetcher updates your `data/sermons.json` file with this format:

```json
{
  "title": "Sunday Sermons",
  "description": "Weekly sermons from our Sunday worship services",
  "sermons": [
    {
      "id": "24-11-10",
      "title": "Sermon Title",
      "author": "Rev. Craig Luekens",
      "scripture": "",
      "date": "2024-11-10",
      "apple_podcasts_url": "https://podcasts.apple.com/...",
      "spotify_url": "https://open.spotify.com/episode/...",
      "link": "https://open.spotify.com/episode/...",
      "podcast_thumbnail_url": "https://...",
      "youtube_url": "",
      "source": "spotify",
      "original_id": "episode_id"
    }
  ]
}
```

## Features in Detail

### Smart Merging
- Avoids duplicate entries based on sermon ID
- Updates existing entries with new data (e.g., adds Spotify URL if missing)
- Preserves manual fields like scripture and author

### Error Handling
- Continues processing if one source fails
- Logs all errors for debugging
- Graceful handling of network issues

### Rate Limiting
- Respects API rate limits
- Includes delays between requests
- Handles pagination automatically

### Data Extraction
- Extracts episode IDs from various URL formats
- Converts dates to consistent format
- Handles different thumbnail sources
- Extracts external URLs from descriptions

## Troubleshooting

### Common Issues

1. **Spotify Authentication Failed**
   - Check your Client ID and Secret
   - Ensure your app is properly configured
   - Verify the show IDs are correct

2. **RSS Feed Not Accessible**
   - Test the RSS URL in your browser
   - Check if the podcast is public
   - Verify the URL format

3. **No New Episodes Found**
   - Check if episodes are published
   - Verify the show ID or RSS URL
   - Check the logs for errors

### Logs

Check the console output or `podcast_scheduler.log` for detailed information about the fetching process.

## Advanced Usage

### Custom Data Mapping

You can modify `podcast_fetcher.py` to customize how data is mapped to your sermon format:

```python
def convert_to_sermon_format(self, episodes, source):
    # Customize this method to match your needs
    pass
```

### Multiple Podcast Sources

Add multiple shows or RSS feeds to your configuration:

```json
{
  "spotify": {
    "show_ids": ["show1", "show2", "show3"]
  },
  "anchor": {
    "rss_urls": ["rss1", "rss2", "rss3"]
  }
}
```

### Custom Scheduling

Modify the scheduler to run at different intervals or times:

```python
# In podcast_scheduler.py
schedule.every().day.at("02:00").do(self.run_fetch)  # Daily at 2 AM
schedule.every().monday.do(self.run_fetch)  # Weekly on Monday
```

## Support

If you encounter issues:

1. Check the logs for error messages
2. Verify your API credentials
3. Test your RSS URLs manually
4. Ensure all dependencies are installed

The system is designed to be robust and will continue working even if some sources fail.
