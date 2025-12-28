# Sunday Sermon Archive Guide

This guide explains how to add historical sermon archive data to the Sunday Sermon archive on the website.

## Overview

The sermon archive system uses a master JSON file (`data/sermons.json`) that contains all sermons, both current and historical. The archive data is integrated seamlessly with the existing sermon display system.

## File Structure

- **`data/sermons.json`** - Master JSON file containing all sermons
- **`ingest_sermon_archive.py`** - Script to parse and ingest archive data
- **`data/sermon_archive_*.tsv`** - Tab-separated input files for archive data

## Adding Archive Data

### Step 1: Prepare Your Data

Create a tab-separated (TSV) file with the following columns:

- **Podcast** - Usually "The Sunday Sermon"
- **Show** - Usually "The Sunday Sermon"
- **Series** - Series name (e.g., "Jude", "True Spirituality") or leave empty
- **Episode** - Episode number within series (optional)
- **Episode_Absolute** - Absolute episode number (optional)
- **Title** - Sermon title
- **Speaker** - Speaker/author name
- **Date** - Date in M/D/YYYY format (e.g., "1/1/2002" or "01/01/2002")
- **Scripture** - Bible reference (e.g., "Jude 1-2", "John 15:1-17")

Example:
```
Podcast	Show	Series	Episode	Episode_Absolute	Title	Speaker	Date	Scripture
The Sunday Sermon	The Sunday Sermon	Jude	1		God Preserves the Remnant	Rev. Preston Graham	1/1/2002	Jude 1-2
The Sunday Sermon	The Sunday Sermon	Jude	2		Contend for the Truth	Rev. Preston Graham	1/8/2002	Jude 3-4
```

### Step 2: Run the Ingestion Script

```bash
python ingest_sermon_archive.py data/sermon_archive_YYYY.tsv --append --output data/sermons.json
```

Options:
- `--append` - Append to existing sermons (recommended)
- `--output <file>` - Specify output file (default: `data/sermons.json`)
- `--archive` - Create separate archive file instead of merging

### Step 3: Verify the Data

Check that the sermons appear correctly:
1. The script will output how many sermons were parsed and added
2. Check `data/sermons.json` to verify the entries
3. Test on the website at `/sermons` to ensure they display correctly

## Data Format

Each sermon in the JSON file has the following structure:

```json
{
  "id": "02-01-01",
  "title": "God Preserves the Remnant",
  "author": "Rev. Preston Graham",
  "scripture": "Jude 1-2",
  "date": "2002-01-01",
  "apple_podcasts_url": "",
  "spotify_url": "",
  "youtube_url": "",
  "link": "",
  "podcast_thumbnail_url": "",
  "source": "archive",
  "series": "Jude",
  "episode_title": "God Preserves the Remnant",
  "sermon_type": "sermon",
  "tags": ["Jude"],
  "search_keywords": "god preserves the remnant rev. preston graham jude 1-2 jude",
  "episode_number": 1
}
```

### ID Generation

Sermon IDs are generated automatically in the format `YY-MM-DD` (e.g., `02-01-01` for January 1, 2002). If multiple sermons share the same date, a suffix is added (e.g., `02-01-01-1`, `02-01-01-2`).

### Date Format

- Input: M/D/YYYY or MM/DD/YYYY (e.g., "1/1/2002" or "01/01/2002")
- Output: YYYY-MM-DD (e.g., "2002-01-01")

### Series Handling

- If a Series is provided, it's used as the series name
- If no Series is provided, "The Sunday Sermon" is used as the default
- Series names are also added as tags for filtering

### Scripture Tags

The script automatically extracts book names from scripture references and adds them as tags. For example, "Jude 1-2" will add "Jude" as a tag.

## Bulk Import Process

For importing multiple years of data:

1. **Organize by year**: Create separate TSV files for each year (e.g., `sermon_archive_2002.tsv`, `sermon_archive_2003.tsv`)

2. **Import sequentially**: Run the script for each year:
   ```bash
   python ingest_sermon_archive.py data/sermon_archive_2002.tsv --append
   python ingest_sermon_archive.py data/sermon_archive_2003.tsv --append
   python ingest_sermon_archive.py data/sermon_archive_2004.tsv --append
   # ... and so on
   ```

3. **Verify totals**: After each import, check that the sermon count increased correctly

## Integration with Website

The archive data is automatically integrated with the existing sermon display system:

- **Sermons Page** (`/sermons`): All sermons (including archive) are displayed
- **Search**: Archive sermons are searchable by title, author, scripture, and series
- **Sorting**: Archive sermons can be sorted by date, title, or author
- **Filtering**: Archive sermons can be filtered by series and tags

## Troubleshooting

### Duplicate IDs

If you see warnings about duplicate IDs, the script automatically handles them by appending a suffix. This is normal when multiple sermons share the same date.

### Invalid Dates

If a date cannot be parsed, the entry will be skipped with a warning. Check your date format and ensure it's M/D/YYYY or MM/DD/YYYY.

### Missing Fields

- **Title**: Required - entries without titles are skipped
- **Speaker**: Required - entries without speakers are skipped
- **Date**: Required - entries without valid dates are skipped
- **Scripture**: Optional - can be empty
- **Series**: Optional - defaults to "The Sunday Sermon"

## Notes

- The script preserves existing sermons when using `--append`
- Sermons are automatically sorted by date (newest first) after import
- The archive data uses `"source": "archive"` to distinguish from current sermons
- All archive sermons are marked as `"sermon_type": "sermon"` by default

## Example: Importing 2002-2003 Data

```bash
# Import 2002 data
python ingest_sermon_archive.py data/sermon_archive_2002_2003.tsv --append

# Verify
grep -c '"date": "2002-' data/sermons.json
grep -c '"date": "2003-' data/sermons.json
```

## Future Enhancements

Potential improvements for future versions:
- Support for CSV format in addition to TSV
- Automatic date correction for sequential Sundays
- Bulk import from Excel files
- Validation and data quality checks
- Preview mode before committing changes

