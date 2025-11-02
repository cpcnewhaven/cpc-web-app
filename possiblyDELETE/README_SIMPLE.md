# CPC New Haven - Simple JSON-Based Website

A sleek, modern church website built with Flask and JSON file storage. Features a beautiful glass morphism design and easy content management.

## ✨ Features

- **Glass Morphism Design**: Modern, sleek UI with glass-like effects
- **JSON Data Storage**: No database required - everything stored in simple JSON files
- **Easy Content Management**: Simple admin interface for managing content
- **Responsive Design**: Works perfectly on all devices
- **Fast & Lightweight**: Minimal dependencies, fast loading

## 🚀 Quick Start

### Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements_simple.txt
   ```

2. **Run the Application**
   ```bash
   python app_simple.py
   ```

3. **Visit the Website**
   - Main site: http://localhost:5000
   - Admin panel: http://localhost:5000/admin

### Deploy to Render.com

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Render**
   - Go to [render.com](https://render.com)
   - Connect your GitHub repository
   - Use these settings:
     - **Build Command**: `pip install -r requirements_simple.txt`
     - **Start Command**: `python app_simple.py`
     - **Environment**: Python 3

## 📁 Project Structure

```
cpc-web-app/
├── app_simple.py              # Main Flask application
├── json_data.py               # JSON data management
├── requirements_simple.txt    # Python dependencies
├── data/                      # JSON data files
│   ├── announcements.json
│   ├── sermons.json
│   ├── events.json
│   ├── podcast_series.json
│   ├── podcast_episodes.json
│   └── gallery.json
├── static/css/
│   └── glass.css              # Glass morphism styles
├── templates/
│   ├── base_glass.html        # Glass base template
│   ├── index_glass.html       # Homepage
│   ├── admin_glass.html       # Admin interface
│   └── ...                    # Other pages
└── README_SIMPLE.md
```

## 🎨 Design System

### Glass Morphism Components
- **Glass Cards**: Translucent cards with blur effects
- **Glass Buttons**: Interactive buttons with hover effects
- **Glass Navigation**: Floating navigation bar
- **Glass Forms**: Beautiful form inputs

### Color Palette
- **Primary Blue**: #0078D4
- **Glass White**: rgba(255, 255, 255, 0.25)
- **Glass Black**: rgba(0, 0, 0, 0.1)
- **Gradients**: Modern gradient backgrounds

## 📝 Content Management

### Adding Content

1. **Via Admin Interface**
   - Go to `/admin`
   - Click "Add [Content Type]"
   - Fill out the form
   - Save

2. **Via JSON Files**
   - Edit files in `/data/` directory
   - Add new items following existing format
   - Restart application

### Content Types

- **Announcements**: Church announcements and updates
- **Sermons**: Sunday sermons with audio/video links
- **Events**: Church events and activities
- **Podcast Series**: Podcast series information
- **Podcast Episodes**: Individual podcast episodes
- **Gallery**: Photo gallery with tags

## 🔧 Customization

### Styling
- Edit `static/css/glass.css` for design changes
- Modify CSS variables for color scheme
- Add new glass components as needed

### Content
- Update JSON files in `/data/` directory
- Modify templates in `/templates/` directory
- Add new routes in `app_simple.py`

### Features
- Add new content types in `json_data.py`
- Create new admin forms in `admin_glass.html`
- Add new API endpoints in `app_simple.py`

## 📱 Pages

- **Home** (`/`): Welcome page with highlights
- **Sundays** (`/sundays`): Service information
- **About** (`/about`): Church information
- **Podcasts** (`/podcasts`): Sermon podcasts
- **Events** (`/events`): Upcoming events
- **Community** (`/community`): Church community
- **Live** (`/live`): Live streaming
- **Resources** (`/resources`): Church resources
- **Give** (`/give`): Giving information
- **Admin** (`/admin`): Content management

## 🚀 Deployment

### Render.com (Recommended)

1. **Create render.yaml** (already included)
2. **Connect GitHub repository**
3. **Deploy automatically**

### Other Platforms

- **Heroku**: Use `Procfile` and `requirements_simple.txt`
- **DigitalOcean**: Use Docker or direct Python deployment
- **Vercel**: Use Python runtime
- **Railway**: Direct GitHub integration

## 🔒 Security

- **Secret Key**: Set `SECRET_KEY` environment variable
- **File Permissions**: Ensure JSON files are writable
- **Admin Access**: Consider adding authentication for production

## 📊 Performance

- **Fast Loading**: Minimal dependencies
- **Cached Data**: JSON files loaded once per request
- **Optimized CSS**: Modern CSS with hardware acceleration
- **Responsive Images**: Optimized image handling

## 🛠️ Troubleshooting

### Common Issues

1. **JSON File Errors**
   - Check JSON syntax
   - Ensure proper file permissions
   - Validate data structure

2. **Styling Issues**
   - Clear browser cache
   - Check CSS file paths
   - Verify font loading

3. **Admin Interface**
   - Check browser console for errors
   - Verify form data format
   - Test API endpoints

### Debug Mode

```bash
export FLASK_ENV=development
python app_simple.py
```

## 📞 Support

For issues or questions:
1. Check this README
2. Review error logs
3. Test locally first
4. Check JSON file format

## 🎯 Next Steps

- Add user authentication
- Implement image uploads
- Add email notifications
- Create mobile app
- Add analytics tracking

---

**Built with ❤️ for Christ Presbyterian Church New Haven**
