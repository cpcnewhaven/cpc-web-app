# CPC New Haven - Flask Web Application

A modern Flask web application for Christ Presbyterian Church New Haven, featuring dynamic content management, sermon archives, podcast integration, and responsive design.

## Features

- **Dynamic Content Management**: Admin interface for managing announcements, sermons, and events
- **Sermon Archives**: Searchable and filterable sermon library with multiple viewing options
- **Podcast Integration**: Multiple podcast series with episode management
- **Responsive Design**: Mobile-first design with Alpine.js for interactive components
- **API-First Architecture**: RESTful API endpoints for all content types
- **Image Gallery**: Dynamic image management with tagging and categorization

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-Migrate
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML5, CSS3, Alpine.js, Vanilla JavaScript
- **Admin Interface**: Flask-Admin
- **Deployment**: Ready for Heroku, Docker, or traditional hosting

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd cpc-web-app
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
# Create database tables
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Load sample data
python migrate_data.py
```

### 5. Run the Application

```bash
python app.py
```

Visit `http://localhost:5000` to see the website and `http://localhost:5000/admin` for the admin interface.

## Project Structure

```
cpc-web-app/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── config.py              # Configuration settings
├── migrate_data.py        # Sample data migration
├── requirements.txt       # Python dependencies
├── templates/             # Jinja2 templates
│   ├── base.html         # Base template
│   ├── index.html        # Homepage
│   ├── sermons.html      # Sermons page
│   ├── podcasts.html     # Podcasts page
│   └── about.html        # About page
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   ├── js/               # JavaScript files
│   └── assets/           # Images and media
└── migrations/           # Database migrations (auto-generated)
```

## API Endpoints

### Content APIs
- `GET /api/announcements` - Get all active announcements
- `GET /api/sermons` - Get all sermons
- `GET /api/podcasts/beyond-podcast` - Beyond the Sunday Sermon episodes
- `GET /api/podcasts/biblical-interpretation` - Biblical Interpretation episodes
- `GET /api/podcasts/confessional-theology` - Confessional Theology episodes
- `GET /api/podcasts/membership-seminar` - Membership Seminar episodes
- `GET /api/gallery` - Get gallery images
- `GET /api/ongoing-events` - Get ongoing events

### Page Routes
- `GET /` - Homepage
- `GET /sermons` - Sermons page
- `GET /podcasts` - Podcasts page
- `GET /about` - About page
- `GET /admin` - Admin interface

## Database Models

### Announcement
- `id` (String, Primary Key)
- `title` (String)
- `description` (Text)
- `date_entered` (DateTime)
- `active` (Boolean)
- `type` (String) - event, announcement, ongoing
- `category` (String)
- `tag` (String)
- `superfeatured` (Boolean)
- `featured_image` (String)

### Sermon
- `id` (String, Primary Key)
- `title` (String)
- `author` (String)
- `scripture` (String)
- `date` (Date)
- `spotify_url` (String)
- `youtube_url` (String)
- `apple_podcasts_url` (String)
- `podcast_thumbnail_url` (String)

### PodcastSeries
- `id` (Integer, Primary Key)
- `title` (String)
- `description` (Text)

### PodcastEpisode
- `id` (Integer, Primary Key)
- `series_id` (Integer, Foreign Key)
- `number` (Integer)
- `title` (String)
- `link` (String)
- `guest` (String)
- `date_added` (Date)
- `scripture` (String)
- `podcast_thumbnail_url` (String)

### GalleryImage
- `id` (String, Primary Key)
- `name` (String)
- `url` (String)
- `tags` (JSON)
- `event` (Boolean)
- `created` (DateTime)

### OngoingEvent
- `id` (String, Primary Key)
- `title` (String)
- `description` (Text)
- `date_entered` (DateTime)
- `active` (Boolean)
- `type` (String)
- `category` (String)

## Admin Interface

Access the admin interface at `/admin` to manage:
- Announcements and highlights
- Sermon archives
- Podcast series and episodes
- Gallery images
- Ongoing events

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///cpc_newhaven.db
```

### Production Database

For production, update the `DATABASE_URL` to use PostgreSQL:

```env
DATABASE_URL=postgresql://username:password@localhost/cpc_newhaven
```

## Deployment

### Heroku

1. Create a `Procfile`:
```
web: gunicorn app:app
```

2. Add PostgreSQL addon:
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

3. Deploy:
```bash
git push heroku main
heroku run python migrate_data.py
```

### Docker

1. Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

2. Build and run:
```bash
docker build -t cpc-web-app .
docker run -p 5000:5000 cpc-web-app
```

## Development

### Adding New Content Types

1. Create model in `models.py`
2. Add admin view in `app.py`
3. Create API endpoint
4. Update templates as needed

### Customizing Styles

Edit `static/css/style.css` to customize the appearance. The CSS is organized by component and includes responsive design.

### Adding JavaScript Functionality

Place new JavaScript files in `static/js/` and include them in templates using the `{% block scripts %}` section.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or support, please contact the development team or create an issue in the repository.