# Mailchimp Integration Setup Guide

This guide will help you set up Mailchimp integration for your CPC Weekly Newsletter to automatically display on your website.

## 🚀 Quick Setup (RSS Method - Recommended)

### Step 1: Enable RSS Feed in Mailchimp

1. **Log into your Mailchimp account**
2. **Go to your Audience** (the list you send the CPC Weekly to)
3. **Click on "Settings" → "Audience name and defaults"**
4. **Scroll down to "RSS feed"**
5. **Check "Enable RSS feed"**
6. **Copy the RSS feed URL** (it will look like: `https://us21.campaign-archive.com/feed?u=YOUR_USER_ID&id=YOUR_LIST_ID`)

### Step 2: Configure Your App

1. **Edit `config.py`:**
   ```python
   MAILCHIMP_RSS_URL = "https://us21.campaign-archive.com/feed?u=YOUR_USER_ID&id=YOUR_LIST_ID"
   ```

2. **Restart your Flask app:**
   ```bash
   flask run
   ```

3. **Test the integration:**
   - Visit `/mailchimp-newsletter` to see your newsletter
   - Visit `/api/mailchimp` to see raw data
   - Visit `/data-dashboard` to monitor all sources

## 🔧 Advanced Setup (API Method)

If you want more control or the RSS method doesn't work, you can use the Mailchimp API:

### Step 1: Get API Credentials

1. **Go to Mailchimp Account → Extras → API Keys**
2. **Create a new API key**
3. **Copy the API key** (starts with something like `abc123def456...`)
4. **Find your server prefix** (e.g., `us21`, `us12`, etc.) - it's in your API key or account settings

### Step 2: Get List ID

1. **Go to Audience → Settings → Audience name and defaults**
2. **Copy the "Audience ID"** (looks like `abc123def456`)

### Step 3: Configure Environment Variables

Create a `.env` file in your project root:
```env
MAILCHIMP_API_KEY=your_api_key_here
MAILCHIMP_SERVER_PREFIX=us21
MAILCHIMP_LIST_ID=your_list_id_here
```

### Step 4: Update Config

Edit `config.py` to use environment variables:
```python
MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY")
MAILCHIMP_SERVER_PREFIX = os.getenv("MAILCHIMP_SERVER_PREFIX")
MAILCHIMP_LIST_ID = os.getenv("MAILCHIMP_LIST_ID")
```

## 🎯 Webhook Setup (Real-time Updates)

For instant updates when you send newsletters:

### Step 1: Set Up Webhook

1. **Go to Mailchimp → Audience → Settings → Webhooks**
2. **Click "Create Webhook"**
3. **Set the webhook URL to:** `https://your-domain.com/webhooks/mailchimp`
4. **Select events:** Check "Campaign sent"
5. **Save the webhook**

### Step 2: Test Webhook

1. **Send a test newsletter**
2. **Check your server logs** for webhook calls
3. **Visit `/api/mailchimp/latest`** to see the latest newsletter

## 📊 What You'll Get

### Newsletter Content
- **Title:** Cleaned up newsletter titles (removes "CPC Weekly Highlights" prefixes)
- **Content:** Formatted newsletter content with proper styling
- **Images:** Extracted from newsletters
- **Links:** Direct links to full newsletters
- **Dates:** Publication dates

### API Endpoints
- `/api/mailchimp` - Latest newsletter content
- `/api/mailchimp/latest` - Latest from webhook
- `/webhooks/mailchimp` - Webhook endpoint
- `/mailchimp-newsletter` - Newsletter display page

### Data Dashboard
- Real-time status of Mailchimp integration
- Recent newsletter items
- Error monitoring and troubleshooting

## 🎨 Customization

### Newsletter Display
The newsletter template (`mailchimp_newsletter.html`) includes:
- **Clean formatting** for church newsletters
- **Responsive design** for mobile and desktop
- **CPC branding** and styling
- **Content parsing** for better readability

### Content Processing
The Mailchimp ingester automatically:
- **Removes Mailchimp footers** and boilerplate text
- **Cleans up titles** (removes "CPC Weekly Highlights" prefixes)
- **Extracts images** from newsletters
- **Formats content** for web display

## 🔍 Troubleshooting

### Common Issues

**"Mailchimp not configured"**
- Make sure you've set either `MAILCHIMP_RSS_URL` or the API credentials
- Check that the RSS URL is correct and accessible

**"Failed to fetch from RSS"**
- Verify the RSS feed URL is correct
- Check that the RSS feed is enabled in Mailchimp
- Try accessing the RSS URL directly in your browser

**"Failed to fetch from API"**
- Verify your API key is correct
- Check that the server prefix matches your account
- Ensure the list ID is correct

**Webhook not working**
- Check that the webhook URL is accessible from the internet
- Verify the webhook is set to "Campaign sent" events
- Check server logs for webhook errors

### Testing Individual Components

```bash
# Test RSS feed
curl "https://us21.campaign-archive.com/feed?u=YOUR_USER_ID&id=YOUR_LIST_ID"

# Test API endpoint
curl http://localhost:5000/api/mailchimp

# Test webhook (simulate)
curl -X POST http://localhost:5000/webhooks/mailchimp \
  -H "Content-Type: application/json" \
  -d '{"data": {"id": "test-campaign-id"}}'
```

## 📈 Monitoring

### Data Dashboard
Visit `/data-dashboard` to see:
- Mailchimp integration status
- Recent newsletter items
- Error messages and troubleshooting
- Last updated timestamps

### Logs
Check your server logs for:
- Webhook calls and responses
- API errors and timeouts
- Content processing issues

## 🚀 Next Steps

### Content Optimization
- **Add images** to your newsletters for better display
- **Use consistent formatting** for better parsing
- **Include clear titles** for better organization

### Advanced Features
- **Set up multiple lists** for different newsletter types
- **Add content filtering** for specific newsletter sections
- **Implement email notifications** for new newsletters

### Integration with Existing Content
- **Link to newsletter** from your homepage
- **Add newsletter signup** forms
- **Include newsletter archive** in your site navigation

## 📞 Support

If you need help:
1. **Check the data dashboard** at `/data-dashboard`
2. **Test individual API endpoints** for error details
3. **Check server logs** for detailed error information
4. **Verify Mailchimp settings** and permissions

The system is designed to be resilient - if Mailchimp is unavailable, other content sources continue working normally.
