# AI Documentation - Ship Tracker Application

## Overview

This is a Flask-based web application that tracks the location of the cargo ship "Sagittarius Leader" by scraping location data from shipnext.com. The application displays the ship's position on an interactive map, stores location history in a SQLite database, and provides both automated scheduled updates and manual update capabilities.

## Project Structure

```
/workspace/
├── app.py              # Flask web server and REST API
├── scraper.py          # Web scraping module for shipnext.com
├── scheduler.py        # Background task scheduler for automated updates
├── requirements.txt    # Python dependencies
├── ship_locations.db   # SQLite database (created at runtime)
└── static/
    ├── index.html      # Main HTML page
    ├── app.js          # Frontend JavaScript (map, API calls)
    └── styles.css      # CSS styling
```

## Architecture

### Component Flow

```
User Browser
    ↓
Frontend (index.html, app.js)
    ↓ HTTP requests
Flask Server (app.py)
    ↓
├──→ API Endpoints → Database (SQLite)
└──→ Manual Update → Scraper (scraper.py)
    
Background Scheduler (scheduler.py)
    ↓ (daily at 00:00 UTC)
Scraper (scraper.py)
    ↓
HTTP Request → shipnext.com
    ↓
Parse HTML → Extract coordinates
    ↓
Database (SQLite)
```

## Core Components

### 1. app.py - Flask Web Server

**Purpose**: Main Flask application that serves the web interface and provides REST API endpoints.

**Key Functions**:
- `init_db()`: Initializes SQLite database with `ship_locations` table
- `index()`: Serves the main HTML page (index.html)
- `get_location()`: GET endpoint `/api/location` - Returns latest ship location
- `get_history()`: GET endpoint `/api/history` - Returns last 30 location entries
- `manual_update()`: POST endpoint `/api/update` - Triggers manual scrape and database update

**Database Schema**:
```sql
CREATE TABLE ship_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ship_name TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    timestamp TEXT NOT NULL,
    location_text TEXT,
    speed REAL,
    heading REAL
)
```

**Configuration**:
- Static folder: `static/`
- Database path: `ship_locations.db`
- Server: Runs on `0.0.0.0:3000` in debug mode
- CORS: Enabled for cross-origin requests

**API Endpoints**:
- `GET /` - Serves index.html
- `GET /static/<filename>` - Serves static files (JS, CSS)
- `GET /api/location` - Returns latest location for "Sagittarius Leader"
- `GET /api/history` - Returns last 30 location entries
- `POST /api/update` - Manually triggers location scrape and database update

**Response Format**:
```json
{
  "success": true,
  "latitude": 40.7128,
  "longitude": -74.0060,
  "timestamp": "2024-01-01T12:00:00",
  "location_text": "New York",
  "speed": 15.5,
  "heading": 180.0
}
```

### 2. scraper.py - Web Scraping Module

**Purpose**: Scrapes shipnext.com to extract ship location data including coordinates, location text, speed, and heading.

**Target URL**: `https://shipnext.com/vessel/9283887-sagittarius-leader`

**Key Functions**:

1. **`scrape_ship_location(ship_name)`**
   - Main entry point for scraping
   - Fetches HTML from shipnext.com vessel page
   - Parses HTML with BeautifulSoup
   - Returns dictionary with location data

2. **`extract_from_shipnext_detail(soup, ship_name, response_text=None)`**
   - Extracts location data from vessel detail page HTML
   - Multiple extraction strategies:
     - JavaScript variables (lat/lng in script tags)
     - Text patterns ("Vessel's current position is...")
     - DMS coordinates (degrees/minutes/seconds)
     - Decimal coordinates
     - Destination port patterns
   - Geocodes location text if coordinates not found
   - Returns dict: `{latitude, longitude, location_text, speed, heading}`

3. **`extract_coordinates_after_position_string(text)`**
   - Looks for pattern: "Vessel's current position is" followed by coordinates
   - Supports DMS and decimal formats
   - Returns tuple `(latitude, longitude)` or `(None, None)`

4. **`extract_dms_coordinates_from_text(text)`**
   - Extracts coordinates in Degrees/Minutes/Seconds format
   - Supports multiple DMS formats:
     - `40°42'46"N`
     - `40° 42' 46" N`
     - `051° 18' 06" N / 003° 14' 14" E` (slash-separated)
     - `40°42'46"N, 74°00'21"W` (comma-separated)
   - Returns tuple `(latitude, longitude)` or `(None, None)`

5. **`parse_dms_to_decimal(dms_str)`**
   - Converts DMS string to decimal degrees
   - Handles N/S/E/W hemisphere indicators
   - Returns tuple `(decimal_degrees, hemisphere)` or `None`

6. **`extract_coordinates_from_text(text)`**
   - Fallback coordinate extraction
   - Tries DMS first, then decimal format
   - Returns tuple `(latitude, longitude)` or `(None, None)`

7. **`geocode_location(location_text)`**
   - Uses geopy/Nominatim to convert location text to coordinates
   - Rate-limited (1 second delay)
   - Returns tuple `(latitude, longitude)` or `(None, None)`

**Extraction Strategy Priority**:
1. JavaScript variables in script tags
2. "Vessel's current position is" pattern
3. DMS coordinates in text
4. Decimal coordinates in text
5. Destination port patterns + geocoding

**Coordinate Validation**:
- Latitude: -90 to 90
- Longitude: -180 to 180
- Invalid coordinates are rejected

### 3. scheduler.py - Background Task Scheduler

**Purpose**: Automatically updates ship location in database at scheduled intervals.

**Key Functions**:

1. **`update_ship_location()`**
   - Calls `scrape_ship_location()` to fetch latest data
   - Inserts location data into SQLite database
   - Handles errors gracefully with logging
   - Prints status messages to console

2. **`start_scheduler()`**
   - Initializes APScheduler BackgroundScheduler
   - Schedules daily job at 00:00 UTC (midnight)
   - Starts scheduler in background thread
   - Runs initial update immediately on startup

**Scheduler Configuration**:
- Type: Cron job (APScheduler)
- Schedule: Daily at 00:00 UTC
- Job ID: `daily_ship_update`
- Runs: Background thread (non-blocking)

**Database Path**: Uses same `ship_locations.db` as Flask app

### 4. Frontend Components

#### index.html
- Structure: Header, controls, info panel, map container, history panel
- Dependencies: Leaflet.js (CDN), custom CSS/JS
- Key Elements:
  - `#map` - Leaflet map container
  - `#updateBtn` - Manual update button
  - `#refreshBtn` - Refresh map button
  - `#status` - Status message display
  - Info panel: lastUpdated, locationText, speed, heading, coordinates
  - `#historyList` - Location history container

#### app.js
**Key Functions**:

1. **`initMap()`**
   - Initializes Leaflet map with OpenStreetMap tiles
   - Sets default view to [0, 0] zoom level 2

2. **`updateMap(locationData)`**
   - Updates map marker with ship location
   - Creates custom SVG cargo ship icon
   - Centers map on ship coordinates
   - Updates info panel

3. **`fetchLocation()`**
   - Fetches latest location from `/api/location`
   - Updates map on success
   - Shows error messages on failure

4. **`manualUpdate()`**
   - Triggers `/api/update` POST request
   - Updates map with new data
   - Refreshes history list

5. **`fetchHistory()`**
   - Fetches last 30 entries from `/api/history`
   - Displays clickable history items
   - Clicking history item centers map on that location

6. **`updateInfoPanel(data)`**
   - Updates all info panel fields
   - Formats timestamp, coordinates, speed, heading

7. **`showStatus(message, type)`**
   - Displays status messages (success/error/loading)
   - Auto-hides after 5 seconds (except loading)

**Auto-refresh**: Fetches location every 5 minutes automatically

#### styles.css
- Modern gradient design (purple/blue theme)
- Responsive grid layout
- Custom cargo ship marker styling with floating animation
- Status message styling (success/error/loading)

## Data Flow

### Initialization Flow
1. `app.py` starts → `init_db()` creates database
2. `start_scheduler()` called → Background scheduler starts
3. Scheduler runs initial `update_ship_location()`
4. Scraper fetches data from shipnext.com
5. Data stored in database
6. Flask server starts listening on port 3000

### User Request Flow
1. User opens browser → `GET /` → Serves `index.html`
2. Browser loads `app.js` → `initMap()` initializes map
3. `fetchLocation()` called → `GET /api/location`
4. Flask queries database → Returns latest location
5. `updateMap()` displays ship on map

### Manual Update Flow
1. User clicks "Update Destination Now" → `manualUpdate()` called
2. `POST /api/update` → Flask calls `scrape_ship_location()`
3. Scraper fetches fresh data from shipnext.com
4. Data inserted into database
5. Response returned with new location data
6. Map updates with new location

### Scheduled Update Flow
1. Scheduler triggers at 00:00 UTC → `update_ship_location()` called
2. Scraper fetches data from shipnext.com
3. Data inserted into database
4. No user action required (automatic)

## Dependencies

### Python (requirements.txt)
- `flask==3.0.0` - Web framework
- `flask-cors==4.0.0` - CORS support
- `requests==2.31.0` - HTTP requests for scraping
- `beautifulsoup4==4.12.2` - HTML parsing
- `lxml==4.9.3` - XML/HTML parser backend
- `apscheduler==3.10.4` - Background task scheduling
- `geopy==2.4.1` - Geocoding support

### Frontend (CDN)
- Leaflet.js 1.9.4 - Map library
- OpenStreetMap tiles - Map tiles

## Configuration Options

### Scheduler (scheduler.py)
- **Update frequency**: Currently daily at 00:00 UTC
- **Change**: Modify `hour` and `minute` parameters in `scheduler.add_job()`
- **Timezone**: UTC (can be changed via APScheduler timezone parameter)

### Flask Server (app.py)
- **Port**: 3000 (change in `app.run()`)
- **Host**: 0.0.0.0 (all interfaces)
- **Debug mode**: Enabled (change `debug=True` to `False` for production)

### Frontend (app.js)
- **Auto-refresh interval**: 5 minutes (300000ms)
- **Change**: Modify `setInterval(fetchLocation, 5 * 60 * 1000)`

### Scraper (scraper.py)
- **Target ship**: Hardcoded as "Sagittarius Leader"
- **Vessel URL**: Hardcoded vessel ID `9283887`
- **Geocoding rate limit**: 1 second delay between requests
- **Request timeout**: 30 seconds
- **User-Agent**: Mozilla/5.0... (to avoid blocking)

## Error Handling

### Scraper Errors
- Network errors: Caught and logged, returns `None`
- Parsing errors: Falls back to next extraction method
- Geocoding errors: Caught and logged, coordinates remain `None`
- Invalid coordinates: Validated before return (rejected if out of range)

### Database Errors
- Connection errors: Would raise exception (not explicitly handled)
- Query errors: Would raise exception (not explicitly handled)
- SQLite auto-creates database file if missing

### API Errors
- Missing data: Returns 404 with `{success: false, message: "No location data found"}`
- Scrape failures: Returns 500 with error message
- Exceptions: Caught and returned as JSON error response

## Database Operations

### Insert (from scheduler.py and app.py)
```python
INSERT INTO ship_locations 
(ship_name, latitude, longitude, timestamp, location_text, speed, heading)
VALUES (?, ?, ?, ?, ?, ?, ?)
```

### Query Latest (from app.py)
```python
SELECT latitude, longitude, timestamp, location_text, speed, heading
FROM ship_locations
WHERE ship_name = ?
ORDER BY timestamp DESC
LIMIT 1
```

### Query History (from app.py)
```python
SELECT latitude, longitude, timestamp, location_text, speed, heading
FROM ship_locations
WHERE ship_name = ?
ORDER BY timestamp DESC
LIMIT 30
```

## Key Design Decisions

1. **SQLite Database**: Lightweight, file-based, no separate server needed
2. **Background Scheduler**: Non-blocking, runs in separate thread
3. **Multiple Extraction Strategies**: Robust scraping with multiple fallbacks
4. **Geocoding Fallback**: Converts location text to coordinates when needed
5. **DMS Coordinate Support**: Handles various coordinate formats from web pages
6. **Custom Ship Icon**: SVG-based cargo ship marker for visual appeal
7. **Auto-refresh**: Frontend automatically updates every 5 minutes
8. **Manual Update**: Allows on-demand updates without waiting for schedule

## Extension Points

### Adding New Ships
1. Modify `scrape_ship_location()` to accept ship URL/vessel ID
2. Update database queries to support multiple ship names
3. Add ship selection UI to frontend
4. Modify API endpoints to accept ship_name parameter

### Adding Features
1. **Email alerts**: Add email notification when ship reaches destination
2. **Route visualization**: Draw path between historical points
3. **Speed/heading visualization**: Show direction vector on map
4. **Multiple data sources**: Add alternative scraping sources for redundancy
5. **Export functionality**: Add CSV/JSON export for location history

## Testing Considerations

### Unit Tests Needed
- `scraper.py`: Test DMS parsing, coordinate extraction, geocoding
- `app.py`: Test API endpoints, database operations
- `scheduler.py`: Test scheduler initialization and job execution

### Integration Tests Needed
- End-to-end scraping workflow
- Database persistence
- API request/response cycles
- Frontend map updates

### Manual Testing
- Verify scraper handles various HTML formats
- Test geocoding with various location strings
- Verify scheduler runs at correct time
- Test error handling for network failures

## Security Considerations

1. **SQL Injection**: Uses parameterized queries (safe)
2. **XSS**: Frontend displays user-controlled data (consider sanitization)
3. **Rate Limiting**: None implemented (could be abused)
4. **CORS**: Enabled for all origins (consider restricting in production)
5. **Input Validation**: Limited validation on API inputs
6. **Scraping Ethics**: Respects robots.txt? (not explicitly checked)

## Production Deployment Notes

1. **Disable debug mode**: Set `debug=False` in `app.run()`
2. **Add error logging**: Use proper logging framework instead of print statements
3. **Database backups**: Implement periodic backups of `ship_locations.db`
4. **Reverse proxy**: Use nginx/Apache in front of Flask
5. **Process management**: Use systemd, supervisor, or Docker
6. **Environment variables**: Move hardcoded values to config/env vars
7. **HTTPS**: Add SSL/TLS certificates
8. **Rate limiting**: Add rate limiting to API endpoints
9. **Monitoring**: Add health check endpoints and monitoring

## Troubleshooting

### Common Issues

1. **No location data**: 
   - Check scraper is extracting data correctly
   - Verify shipnext.com HTML structure hasn't changed
   - Check geocoding is working (API key may be needed)

2. **Scheduler not running**:
   - Verify APScheduler is installed correctly
   - Check background thread is alive
   - Verify cron schedule syntax

3. **Map not displaying**:
   - Check Leaflet.js CDN is accessible
   - Verify OpenStreetMap tiles are loading
   - Check browser console for JavaScript errors

4. **Database errors**:
   - Verify write permissions in directory
   - Check database file isn't locked
   - Verify SQLite is installed

## Maintenance

### Regular Tasks
- Monitor scraper success rate (may need updates if website changes)
- Review database size (consider archiving old entries)
- Update dependencies for security patches
- Check scheduler logs for errors

### Website Changes
If shipnext.com changes their HTML structure:
- Update `extract_from_shipnext_detail()` function
- Test new extraction patterns
- May need to add new extraction strategies
