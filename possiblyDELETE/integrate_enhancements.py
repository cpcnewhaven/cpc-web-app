#!/usr/bin/env python3
"""
Integration Script for Podcast Enhancements
Integrates all the advanced features into your existing Flask app.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def integrate_enhanced_api():
    """Integrate enhanced API endpoints into the main Flask app."""
    logger.info("Integrating enhanced API endpoints...")
    
    # Read the main app.py file
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        # Check if enhanced API is already integrated
        if 'from enhanced_api import enhanced_api' in app_content:
            logger.info("Enhanced API already integrated")
            return True
        
        # Add import statement
        import_line = "from enhanced_api import enhanced_api\n"
        
        # Find where to insert the import (after other imports)
        lines = app_content.split('\n')
        insert_index = 0
        
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                insert_index = i + 1
            elif line.strip() == '' and insert_index > 0:
                break
        
        # Insert the import
        lines.insert(insert_index, import_line)
        
        # Add blueprint registration
        blueprint_line = "app.register_blueprint(enhanced_api, url_prefix='/api')\n"
        
        # Find where to insert blueprint registration (after app creation)
        for i, line in enumerate(lines):
            if 'app = Flask(__name__)' in line:
                # Look for the next non-empty line after app configuration
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() and not lines[j].startswith('#'):
                        lines.insert(j, blueprint_line)
                        break
                break
        
        # Write the updated content
        updated_content = '\n'.join(lines)
        with open('app.py', 'w') as f:
            f.write(updated_content)
        
        logger.info("Enhanced API integrated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to integrate enhanced API: {e}")
        return False

def create_enhanced_templates():
    """Create enhanced templates with advanced search features."""
    logger.info("Creating enhanced templates...")
    
    # Enhanced sermons template with advanced search
    enhanced_sermons_template = '''{% extends "base.html" %}

{% block title %}Sunday Sermons - CPC New Haven{% endblock %}

{% block content %}
<!-- Hero Section -->
<section class="page-hero">
    <div class="container">
        <h1>Sunday Sermons</h1>
        <p>Weekly messages from our Sunday worship services</p>
    </div>
</section>

<!-- Advanced Search Section -->
<section class="search-section">
    <div class="container">
        <div class="search-panel">
            <h3>Advanced Search</h3>
            <form id="advancedSearchForm">
                <div class="search-row">
                    <div class="search-field">
                        <label for="searchQuery">Search</label>
                        <input type="text" id="searchQuery" placeholder="Search sermons, scripture, topics...">
                    </div>
                    <div class="search-field">
                        <label for="authorFilter">Author</label>
                        <select id="authorFilter">
                            <option value="">All Authors</option>
                        </select>
                    </div>
                    <div class="search-field">
                        <label for="seriesFilter">Series</label>
                        <select id="seriesFilter">
                            <option value="">All Series</option>
                        </select>
                    </div>
                </div>
                <div class="search-row">
                    <div class="search-field">
                        <label for="scriptureBook">Scripture Book</label>
                        <input type="text" id="scriptureBook" placeholder="e.g., Luke, John, Romans">
                    </div>
                    <div class="search-field">
                        <label for="scriptureChapter">Chapter</label>
                        <input type="number" id="scriptureChapter" placeholder="e.g., 6">
                    </div>
                    <div class="search-field">
                        <label for="dateRange">Date Range</label>
                        <input type="date" id="startDate" placeholder="Start Date">
                        <input type="date" id="endDate" placeholder="End Date">
                    </div>
                </div>
                <div class="search-actions">
                    <button type="submit" class="btn btn-primary">Search</button>
                    <button type="button" id="clearSearch" class="btn btn-secondary">Clear</button>
                </div>
            </form>
        </div>
    </div>
</section>

<!-- Sermons Section -->
<section class="sermons-section">
    <div class="container">
        <!-- Results Header -->
        <div class="results-header">
            <div class="results-info">
                <span id="resultsCount">0 sermons found</span>
            </div>
            <div class="view-controls">
                <button id="cardView" class="btn btn-sm active">Card View</button>
                <button id="tableView" class="btn btn-sm">Table View</button>
            </div>
            <div class="sort-controls">
                <select id="sortBy">
                    <option value="date">Sort by Date</option>
                    <option value="title">Sort by Title</option>
                    <option value="author">Sort by Author</option>
                </select>
                <button id="sortOrder" class="btn btn-sm">↓</button>
            </div>
        </div>

        <!-- Loading State -->
        <div id="loadingState" class="loading" style="display: none;">
            <p>Searching sermons...</p>
        </div>

        <!-- Results -->
        <div id="searchResults" class="sermons-grid">
            <!-- Results will be populated by JavaScript -->
        </div>

        <!-- No Results -->
        <div id="noResults" class="no-results" style="display: none;">
            <p>No sermons found matching your criteria.</p>
        </div>
    </div>
</section>

<style>
.search-section {
    background: #f8f9fa;
    padding: 2rem 0;
}

.search-panel {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.search-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
}

.search-field {
    flex: 1;
}

.search-field label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
}

.search-field input,
.search-field select {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.search-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
}

.results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding: 1rem 0;
    border-bottom: 1px solid #eee;
}

.sermons-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 2rem;
}

.sermon-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    overflow: hidden;
    transition: transform 0.2s;
}

.sermon-card:hover {
    transform: translateY(-2px);
}

.sermon-thumbnail img {
    width: 100%;
    height: 200px;
    object-fit: cover;
}

.sermon-content {
    padding: 1.5rem;
}

.sermon-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: #333;
}

.sermon-meta {
    color: #666;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}

.sermon-scripture {
    color: #007bff;
    font-style: italic;
    margin-bottom: 1rem;
}

.sermon-links {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    text-decoration: none;
    display: inline-block;
    font-size: 0.9rem;
    cursor: pointer;
}

.btn-primary {
    background: #007bff;
    color: white;
}

.btn-secondary {
    background: #6c757d;
    color: white;
}

.btn-spotify {
    background: #1db954;
    color: white;
}

.btn-youtube {
    background: #ff0000;
    color: white;
}

.btn-apple {
    background: #000;
    color: white;
}

.loading {
    text-align: center;
    padding: 2rem;
    color: #666;
}

.no-results {
    text-align: center;
    padding: 2rem;
    color: #666;
}
</style>

<script>
// Enhanced search functionality
class SermonSearch {
    constructor() {
        this.currentResults = [];
        this.currentView = 'card';
        this.currentSort = 'date';
        this.currentOrder = 'desc';
        
        this.initializeEventListeners();
        this.loadFilters();
    }
    
    initializeEventListeners() {
        document.getElementById('advancedSearchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });
        
        document.getElementById('clearSearch').addEventListener('click', () => {
            this.clearSearch();
        });
        
        document.getElementById('cardView').addEventListener('click', () => {
            this.setView('card');
        });
        
        document.getElementById('tableView').addEventListener('click', () => {
            this.setView('table');
        });
        
        document.getElementById('sortBy').addEventListener('change', (e) => {
            this.currentSort = e.target.value;
            this.sortResults();
        });
        
        document.getElementById('sortOrder').addEventListener('click', () => {
            this.currentOrder = this.currentOrder === 'desc' ? 'asc' : 'desc';
            document.getElementById('sortOrder').textContent = this.currentOrder === 'desc' ? '↓' : '↑';
            this.sortResults();
        });
    }
    
    async loadFilters() {
        try {
            const response = await fetch('/api/search/filters');
            const data = await response.json();
            
            if (data.success) {
                this.populateSelect('authorFilter', data.filters.authors);
                this.populateSelect('seriesFilter', data.filters.series);
            }
        } catch (error) {
            console.error('Error loading filters:', error);
        }
    }
    
    populateSelect(selectId, options) {
        const select = document.getElementById(selectId);
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            select.appendChild(optionElement);
        });
    }
    
    async performSearch() {
        const formData = new FormData(document.getElementById('advancedSearchForm'));
        const params = new URLSearchParams();
        
        // Build search parameters
        const query = document.getElementById('searchQuery').value;
        if (query) params.append('q', query);
        
        const author = document.getElementById('authorFilter').value;
        if (author) params.append('author', author);
        
        const series = document.getElementById('seriesFilter').value;
        if (series) params.append('series', series);
        
        const scriptureBook = document.getElementById('scriptureBook').value;
        if (scriptureBook) params.append('scripture_book', scriptureBook);
        
        const scriptureChapter = document.getElementById('scriptureChapter').value;
        if (scriptureChapter) params.append('scripture_chapter', scriptureChapter);
        
        const startDate = document.getElementById('startDate').value;
        if (startDate) params.append('start_date', startDate);
        
        const endDate = document.getElementById('endDate').value;
        if (endDate) params.append('end_date', endDate);
        
        params.append('sort_by', this.currentSort);
        params.append('sort_order', this.currentOrder);
        
        this.showLoading(true);
        
        try {
            const response = await fetch(`/api/search/sermons?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.currentResults = data.results;
                this.displayResults();
                this.updateResultsCount(data.total);
            } else {
                console.error('Search failed:', data.error);
                this.showNoResults();
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showNoResults();
        } finally {
            this.showLoading(false);
        }
    }
    
    displayResults() {
        const container = document.getElementById('searchResults');
        const noResults = document.getElementById('noResults');
        
        if (this.currentResults.length === 0) {
            container.style.display = 'none';
            noResults.style.display = 'block';
            return;
        }
        
        container.style.display = 'grid';
        noResults.style.display = 'none';
        
        container.innerHTML = this.currentResults.map(sermon => this.renderSermon(sermon)).join('');
    }
    
    renderSermon(sermon) {
        const date = new Date(sermon.date).toLocaleDateString();
        const thumbnail = sermon.podcast_thumbnail_url ? 
            `<div class="sermon-thumbnail">
                <img src="${sermon.podcast_thumbnail_url}" alt="${sermon.title}" loading="lazy">
            </div>` : '';
        
        const links = [];
        if (sermon.spotify_url) links.push(`<a href="${sermon.spotify_url}" target="_blank" class="btn btn-spotify">Spotify</a>`);
        if (sermon.youtube_url) links.push(`<a href="${sermon.youtube_url}" target="_blank" class="btn btn-youtube">YouTube</a>`);
        if (sermon.apple_podcasts_url) links.push(`<a href="${sermon.apple_podcasts_url}" target="_blank" class="btn btn-apple">Apple</a>`);
        
        return `
            <div class="sermon-card">
                ${thumbnail}
                <div class="sermon-content">
                    <h3 class="sermon-title">${sermon.title}</h3>
                    <p class="sermon-meta">
                        <span class="sermon-author">${sermon.author}</span> •
                        <span class="sermon-date">${date}</span>
                    </p>
                    ${sermon.scripture ? `<p class="sermon-scripture">${sermon.scripture}</p>` : ''}
                    <div class="sermon-links">
                        ${links.join('')}
                    </div>
                </div>
            </div>
        `;
    }
    
    sortResults() {
        this.currentResults.sort((a, b) => {
            let aVal = a[this.currentSort] || '';
            let bVal = b[this.currentSort] || '';
            
            if (this.currentSort === 'date') {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
            } else {
                aVal = aVal.toString().toLowerCase();
                bVal = bVal.toString().toLowerCase();
            }
            
            if (this.currentOrder === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
        
        this.displayResults();
    }
    
    setView(view) {
        this.currentView = view;
        
        document.getElementById('cardView').classList.toggle('active', view === 'card');
        document.getElementById('tableView').classList.toggle('active', view === 'table');
        
        // Update grid layout
        const container = document.getElementById('searchResults');
        if (view === 'table') {
            container.style.gridTemplateColumns = '1fr';
        } else {
            container.style.gridTemplateColumns = 'repeat(auto-fill, minmax(300px, 1fr))';
        }
    }
    
    clearSearch() {
        document.getElementById('advancedSearchForm').reset();
        this.currentResults = [];
        this.displayResults();
        this.updateResultsCount(0);
    }
    
    showLoading(show) {
        document.getElementById('loadingState').style.display = show ? 'block' : 'none';
        document.getElementById('searchResults').style.display = show ? 'none' : 'grid';
    }
    
    showNoResults() {
        document.getElementById('searchResults').style.display = 'none';
        document.getElementById('noResults').style.display = 'block';
        this.updateResultsCount(0);
    }
    
    updateResultsCount(count) {
        document.getElementById('resultsCount').textContent = `${count} sermons found`;
    }
}

// Initialize search when page loads
document.addEventListener('DOMContentLoaded', () => {
    new SermonSearch();
});
</script>
{% endblock %}'''

    # Write the enhanced template
    with open('templates/sermons_enhanced.html', 'w') as f:
        f.write(enhanced_sermons_template)
    
    logger.info("Enhanced templates created successfully")

def create_management_scripts():
    """Create management scripts for easy operation."""
    logger.info("Creating management scripts...")
    
    # Daily update script
    daily_update_script = '''#!/bin/bash
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
'''

    with open('daily_update.sh', 'w') as f:
        f.write(daily_update_script)
    
    os.chmod('daily_update.sh', 0o755)
    
    # Weekly analytics script
    weekly_analytics_script = '''#!/bin/bash
# Weekly Analytics Script
# Run this script weekly to generate detailed analytics

echo "📊 Starting weekly analytics..."
cd "$(dirname "$0")"

# Run analytics
python podcast_master.py analytics

# Create backup
python podcast_master.py backup

echo "📈 Weekly analytics completed!"
'''

    with open('weekly_analytics.sh', 'w') as f:
        f.write(weekly_analytics_script)
    
    os.chmod('weekly_analytics.sh', 0o755)
    
    logger.info("Management scripts created successfully")

def main():
    """Main integration function."""
    logger.info("Starting podcast system integration...")
    
    try:
        # Step 1: Integrate enhanced API
        if not integrate_enhanced_api():
            logger.error("Failed to integrate enhanced API")
            return False
        
        # Step 2: Create enhanced templates
        create_enhanced_templates()
        
        # Step 3: Create management scripts
        create_management_scripts()
        
        # Step 4: Run initial enhancement
        logger.info("Running initial data enhancement...")
        from sermon_enhancer import SermonEnhancer
        enhancer = SermonEnhancer()
        enhancer.enhance_all_sermons()
        
        logger.info("🎉 Podcast system integration completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Install new dependencies: pip install -r requirements.txt")
        logger.info("2. Test the enhanced search: python podcast_master.py search --query 'grace'")
        logger.info("3. Run analytics: python podcast_master.py analytics")
        logger.info("4. Set up daily updates: ./daily_update.sh")
        logger.info("5. Access enhanced search at: /sermons_enhanced")
        
        return True
        
    except Exception as e:
        logger.error(f"Integration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
