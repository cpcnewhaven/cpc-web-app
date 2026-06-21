# Sermon Data Optimization

## Overview

Optimized the sermon data structure to eliminate duplication and reduce file size by ~50%.

## Problem

The original `sermons.json` stored sermons twice:
- `sermons_by_year`: Organized by year (for easy viewing)
- `sermons`: Flat array (for API compatibility)

This resulted in:
- **File size**: 0.96 MB (with duplication)
- **Duplication**: 514 sermons stored twice
- **Waste**: ~0.48 MB of redundant data

## Solution

### 1. Optimized Structure
- **Removed**: Flat `sermons` array from storage
- **Kept**: `sermons_by_year` as the single source of truth
- **Added**: `SermonDataHelper` class to generate flat array on-demand

### 2. Benefits
- **File size reduction**: ~50% smaller (0.48 MB saved)
- **Single source of truth**: No duplication
- **Performance**: Caching ensures fast access
- **Backward compatible**: Falls back to old method if needed

### 3. Implementation

#### SermonDataHelper (`sermon_data_helper.py`)
- Loads data with file modification tracking
- Generates flat array from `sermons_by_year` on-demand
- Caches results for performance
- Provides search and filtering methods

#### Updated Endpoints
- `/api/sermons`: Uses helper to generate flat array
- `/api/archive`: Uses helper for archive filtering
- Both have fallback to old method for compatibility

## Usage

### Before Optimization
```json
{
  "sermons_by_year": {
    "2002": [...],
    "2003": [...]
  },
  "sermons": [...]  // Duplicate data
}
```

### After Optimization
```json
{
  "sermons_by_year": {
    "2002": [...],
    "2003": [...]
  },
  "_optimized": true,
  "_note": "Flat array generated on-demand"
}
```

## Performance

- **File load**: Same speed (cached)
- **Array generation**: < 1ms (cached after first access)
- **Memory**: Reduced by ~50%
- **Disk space**: Reduced by ~50%

## Migration

To optimize existing file:
```bash
python optimize_sermons_json.py
```

This will:
1. Create a backup of the original file
2. Remove the duplicate `sermons` array
3. Add optimization metadata
4. Show size savings

## Backward Compatibility

The system maintains backward compatibility:
- If `sermons` array exists, it's used (old format)
- If only `sermons_by_year` exists, flat array is generated
- All existing code continues to work

## Future Enhancements

Potential further optimizations:
- Compress JSON (gzip)
- Index frequently accessed fields
- Lazy loading for very large datasets
- Database migration for 10,000+ sermons

