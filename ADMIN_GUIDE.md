# CPC New Haven - Admin Guide

## Overview

This guide covers the comprehensive admin system for managing all content on the CPC New Haven website. The admin interface provides powerful tools for content management, bulk operations, and data export.

## Accessing the Admin Interface

1. Navigate to `http://localhost:5000/admin` (or your domain + `/admin`)
2. The admin interface is organized into categories:
   - **Content**: Announcements, Events
   - **Media**: Sermons, Podcast Series, Podcast Episodes, Gallery

## Dashboard

The admin dashboard provides:
- **Content Statistics**: Overview of all content types
- **Quick Actions**: One-click creation of new content
- **Recent Content**: Latest announcements and sermons
- **System Information**: Quick links to all management areas

## Content Management

### Announcements

**Features:**
- Create, edit, and delete announcements
- Set announcement types (announcement, event, ongoing, highlight)
- Categorize by ministry area (worship, education, fellowship, etc.)
- Mark as "Super Featured" for homepage prominence
- Set active/inactive status
- Add featured images via URL

**Bulk Operations:**
- Toggle active status for multiple announcements
- Toggle super featured status
- Set category for multiple items
- Bulk delete

**Form Fields:**
- **ID**: Unique identifier (auto-generated or custom)
- **Title**: Announcement headline
- **Description**: Full announcement text (supports HTML)
- **Type**: announcement, event, ongoing, highlight
- **Category**: general, worship, education, fellowship, missions, youth, children
- **Tag**: Custom tag for filtering
- **Active**: Show/hide on website
- **Super Featured**: Display prominently on homepage
- **Featured Image URL**: Image to display with announcement

### Events (Ongoing Events)

**Features:**
- Manage recurring and special events
- Set event types (ongoing, recurring, special)
- Categorize by ministry area
- Toggle active status

**Bulk Operations:**
- Toggle active status
- Bulk delete

### Sermons

**Features:**
- Complete sermon management
- Multiple platform links (Spotify, YouTube, Apple Podcasts)
- Scripture reference tracking
- Author management
- Thumbnail images

**Bulk Operations:**
- Bulk delete sermons

**Form Fields:**
- **ID**: Unique identifier
- **Title**: Sermon title
- **Author**: Speaker name
- **Scripture**: Bible reference
- **Date**: Sermon date
- **Spotify URL**: Link to Spotify episode
- **YouTube URL**: Link to YouTube video
- **Apple Podcasts URL**: Link to Apple Podcasts
- **Thumbnail URL**: Episode thumbnail image

### Podcast Management

#### Podcast Series
- Create and manage podcast series
- Set series descriptions
- View episode counts

#### Podcast Episodes
- Add episodes to series
- Set episode numbers and titles
- Add guest information
- Link to audio files and handouts
- Add scripture references
- Set thumbnail images

**Bulk Operations:**
- Bulk delete episodes

### Gallery Management

**Features:**
- Upload and manage images
- Tag images for organization
- Mark as event photos
- Bulk operations for image management

**Bulk Operations:**
- Toggle event status
- Bulk delete images

## Advanced Features

### Bulk Operations

Most content types support bulk operations:
1. Select multiple items using checkboxes
2. Choose an action from the dropdown
3. Confirm the operation

**Available Actions:**
- Toggle active status
- Toggle featured status
- Set category
- Bulk delete

### Data Export

Export content to CSV format:
- **Announcements**: `/admin/export/announcements`
- **Sermons**: `/admin/export/sermons`

### Content Statistics

Access detailed statistics at `/admin/stats`:
- Content counts by type
- Active vs inactive content
- Content by category
- Recent activity

### Setup Tools

**Create Default Podcast Series:**
- Visit `/admin/setup/podcast-series`
- Creates standard podcast series if they don't exist

## Command Line Management

Use the admin management script for advanced operations:

```bash
# Show content statistics
python admin_management.py stats

# Create sample data
python admin_management.py sample

# Clear all data
python admin_management.py clear

# Reset entire database
python admin_management.py reset
```

## Best Practices

### Content Organization

1. **Use Consistent Naming**: Follow a pattern for IDs and titles
2. **Categorize Properly**: Use appropriate categories for easy filtering
3. **Set Active Status**: Only keep current content active
4. **Use Super Featured Sparingly**: Reserve for most important announcements

### Image Management

1. **Use High-Quality Images**: Ensure images are clear and properly sized
2. **Add Descriptive Tags**: Use consistent tagging for easy organization
3. **Mark Event Photos**: Distinguish between general and event photos

### Regular Maintenance

1. **Review Inactive Content**: Periodically clean up old content
2. **Update Featured Content**: Rotate super featured announcements
3. **Check Links**: Ensure all external links are working
4. **Export Data**: Regular backups of content

## Troubleshooting

### Common Issues

**Form Validation Errors:**
- Check required fields are filled
- Ensure URLs are properly formatted
- Verify date formats

**Bulk Operation Failures:**
- Check that items are selected
- Verify permissions
- Try smaller batches

**Image Display Issues:**
- Verify image URLs are accessible
- Check image format compatibility
- Ensure proper image sizing

### Getting Help

1. Check the application logs for error messages
2. Use the test script to verify functionality
3. Review the API endpoints for data issues
4. Check database connectivity

## Security Notes

- Admin interface should be protected with authentication in production
- Regular backups of the database are recommended
- Monitor admin access logs
- Use strong passwords for admin accounts

## API Integration

The admin system integrates with the public API:
- All content changes are immediately reflected on the website
- API endpoints provide the same data structure as the admin
- Changes are visible without server restart

## Performance Tips

1. **Use Filters**: Filter content lists for better performance
2. **Pagination**: Large datasets are automatically paginated
3. **Search**: Use search functionality instead of browsing large lists
4. **Bulk Operations**: Use bulk operations for efficiency

## Content Workflow

### Adding New Content

1. **Plan Content**: Determine type, category, and priority
2. **Create Content**: Use appropriate admin form
3. **Set Status**: Mark as active when ready
4. **Review**: Check display on website
5. **Maintain**: Update or deactivate as needed

### Managing Existing Content

1. **Regular Review**: Check content lists regularly
2. **Update Status**: Change active status as needed
3. **Bulk Operations**: Use for efficiency
4. **Export Data**: For backup and analysis

This admin system provides comprehensive content management capabilities while maintaining ease of use and powerful functionality for managing the CPC New Haven website.
