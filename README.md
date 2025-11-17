# Ship Tracker - Sagittarius Leader

A web application that scrapes shipnext.com for the destination and location information of the ship "Sagittarius Leader" and displays it on an interactive map with automatic scheduled updates. The application also captures hourly screenshots of itself, accessible at `/screenshots/current.bmp`.

## Project Overview

This application tracks the location and destination of the cargo ship "Sagittarius Leader" by:
- Scraping real-time data from shipnext.com (vessel page: `https://shipnext.com/vessel/9283887-sagittarius-leader`)
- Storing location history in a SQLite database
- Displaying current location on an interactive map using Leaflet.js
- **NEW**: Visualizing the last 20 historical locations as a trail on the map with lines connecting chronologically to show the ship's path
- Providing a toggle control to show/hide the history trail
- Providing REST API endpoints for programmatic access
- Automatically updating location data every 6 hours via scheduled background tasks
- Taking hourly screenshots of the application for monitoring, accessible at `/screenshots/current.bmp` (captured at 1440x960, resized to 960x640)

## Architecture

### Backend (Flask)
- **Framework**: Flask 3.0.0 with CORS enabled
- **Rate Limiting**: Flask-Limiter for API protection and rate control
- **Database**: SQLite (`ship_locations.db`)
- **Scheduler**: APScheduler (BackgroundScheduler) for periodic updates
- **Web Scraping**: BeautifulSoup4 with requests library
- **Geocoding**: Geopy (Nominatim) for converting location names to coordinates
- **Screenshot Automation**: Playwright for capturing application screenshots

### Frontend
- **Map Library**: Leaflet.js 1.9.4
- **Map Tiles**: CartoDB Positron (minimalist light style, similar to Toner Lite)
- **Auto-refresh**: Frontend polls API every 5 minutes
- **UI**: Single-page application with info panel, map, and history sidebar
- **History Trail**: Visual display of last 20 locations as black dots with chronological connecting lines forming a path trail
- **Interactive Controls**: Toggle button to show/hide history trail on map

### Data Flow
1. Scheduler triggers update every 6 hours (also runs on startup)
2. Scraper fetches HTML from shipnext.com vessel page
3. Parser extracts coordinates, destination text, speed, and heading
4. Data is stored in SQLite database
5. Frontend requests data via REST API
6. Map displays current location with marker and info panel

## File Structure

```
/workspace/
├── app.py                    # Flask application with scheduler (single-worker mode)
├── app_no_scheduler.py       # Flask application without scheduler (multi-worker mode)
├── worker.py                 # Standalone scheduler worker (for multi-worker mode)
├── scraper.py                # Web scraping logic for shipnext.com
├── scheduler.py              # Background scheduler for automatic updates
├── screenshot_util.py        # Screenshot capture utility using Playwright
├── gunicorn.conf.py          # Gunicorn production server configuration
├── requirements.txt          # Python dependencies
├── test_destination.py      # Test suite for scraper and database
├── ship_locations.db         # SQLite database (created at runtime)
├── static/
│   ├── index.html           # Main HTML page
│   ├── app.js               # Frontend JavaScript (map, API calls)
│   ├── styles.css           # CSS styling
│   └── screenshots/
│       └── current.bmp      # Latest application screenshot (created at runtime)
└── README.md                # This file
```

## Component Descriptions

### app.py
Main Flask application (single-worker mode) that:
- Initializes SQLite database with `ship_locations` table
- Starts background scheduler for automatic updates
- Configures Flask-Limiter for rate limiting API endpoints
- Serves static files (HTML, CSS, JS)
- Provides REST API endpoints:

### app_no_scheduler.py
Alternative Flask application (multi-worker mode) that:
- Same as app.py but does NOT start the scheduler
- Use this with worker.py running separately
- Allows multiple Gunicorn workers for better scalability
- Provides REST API endpoints:
  - `GET /` - Serves index.html (no rate limit)
  - `GET /api/location` - Returns latest ship location (120 req/min)
  - `GET /api/history` - Returns last 30 location entries (120 req/min)
  - `POST /api/update` - Manually triggers location update (1 req/min)
  - `GET /screenshots/current.bmp` - Serves the latest application screenshot (no rate limit)
- Starts background scheduler on application startup
- Runs on `0.0.0.0:3000` (accessible on all network interfaces)

**Database Schema** (`ship_locations` table):
- `id` (INTEGER PRIMARY KEY)
- `ship_name` (TEXT) - Currently "Sagittarius Leader"
- `latitude` (REAL) - Decimal degrees (-90 to 90)
- `longitude` (REAL) - Decimal degrees (-180 to 180)
- `timestamp` (TEXT) - ISO format datetime string
- `location_text` (TEXT) - Human-readable destination/port name
- `speed` (REAL) - Speed in knots (optional)
- `heading` (REAL) - Heading in degrees 0-360 (optional)

### scraper.py
Web scraping module that extracts ship location data from shipnext.com:
- **Main Function**: `scrape_ship_location(ship_name)` - Returns dict with location data
- **URL**: `https://shipnext.com/vessel/9283887-sagittarius-leader`
- **Extraction Methods**:
  1. Parses HTML structure using BeautifulSoup
  2. Extracts coordinates from "Vessel's current position is" text pattern
  3. Supports DMS (Degrees/Minutes/Seconds) and decimal degree formats
  4. Extracts destination port name from HTML elements and text patterns
  5. Extracts speed and heading from text patterns
  6. Falls back to geocoding if coordinates not found but destination text exists
- **Return Format**: Dictionary with keys: `latitude`, `longitude`, `location_text`, `speed`, `heading`
- **Error Handling**: Returns `None` on failure, prints debug messages to console

### scheduler.py
Background task scheduler using APScheduler:
- **Schedule**: 
  - Ship location updates every 6 hours
  - Screenshot capture every 1 hour
- **Initial Update**: Runs immediately when scheduler starts
- **Singleton Pattern**: Prevents multiple scheduler instances
- **Functions**:
  - `update_ship_location()` - Calls scraper and saves to database
  - `update_screenshot()` - Captures application screenshot using Playwright
- **Thread Safety**: Uses ThreadPoolExecutor with non-daemon threads
- **Shutdown**: Registered with `atexit` for graceful shutdown

**Important**: Scheduler runs in background thread, separate from Flask's main thread.

### worker.py
Standalone scheduler worker process:
- Runs the scheduler independently from web workers
- Use this for multi-worker Gunicorn setups
- Prevents duplicate scheduler instances across workers
- Must be run as a separate background process:
  ```bash
  python3 worker.py &
  ```
- Handles the same scheduled tasks as scheduler.py

### screenshot_util.py
Screenshot capture utility using Playwright:
- **Browser**: Chromium (headless mode)
- **Viewport**: 1440x960
- **Output**: Saves to `static/screenshots/current.bmp` (replaces previous screenshot)
- **Resolution**: Captured at 1440x960, resized to 960x640, saved as BMP format
- **URL**: Screenshot accessible at `/screenshots/current.bmp`
- **Functions**:
  - `take_screenshot(url)` - Captures full-page screenshot of the application
  - `get_screenshot_path()` - Returns path to current screenshot
  - `get_screenshot_timestamp()` - Returns last modified timestamp of screenshot

### static/app.js
Frontend JavaScript that:
- Initializes Leaflet map on page load with CartoDB Positron tiles (minimalist light style)
- Fetches location data from `/api/location`
- Displays ship marker with custom SVG icon
- Updates info panel with location details
- Handles manual updates via button click
- Fetches and displays location history (clickable to view past locations)
- **Renders last 20 historical locations as small black dots on the map**
- **Draws dashed lines connecting historical locations chronologically (oldest to newest) to form a ship trail**
- **Provides toggle control to show/hide the history trail**
- Auto-refreshes location data every 5 minutes
- Shows status messages for user feedback

**Key Functions**:
- `initMap()` - Creates Leaflet map instance
- `updateMap(locationData)` - Updates map marker and info panel
- `fetchLocation()` - GET request to `/api/location`
- `manualUpdate()` - POST request to `/api/update`
- `fetchHistory()` - GET request to `/api/history`
- `updateHistoryTrail()` - Draws last 20 locations as dots with chronological lines connecting each location to the next
- `clearHistoryTrail()` - Removes all history markers and lines from map
- `toggleHistoryTrail()` - Shows/hides history trail based on toggle state

### static/index.html
HTML structure with:
- Info panel showing: Last Updated, Destination, Speed, Heading, Coordinates
- Map container (`<div id="map">`)
- History panel with clickable location entries (collapsible)
- Control buttons: "Get Current Location" and "Center Map"
- **Toggle control: Checkbox to show/hide history trail on map (checked by default)**
- Status message area

### static/styles.css
CSS styling for the application including:
- Modern gradient design with purple/blue theme
- Responsive layout with flexbox
- Custom ship marker with floating animation
- History panel with collapsible functionality
- **Toggle control styling with hover effects**
- **History marker styling (small black dots with white borders)**
- **History line styling (dashed black lines with reduced opacity)**
- Status message indicators (success, error, loading)
- Button hover effects and transitions

## Dependencies

### Python Packages (requirements.txt)
- `flask==3.0.0` - Web framework
- `flask-cors==4.0.0` - CORS support for API
- `flask-limiter==3.5.0` - Rate limiting for API endpoints
- `requests==2.31.0` - HTTP requests for web scraping
- `beautifulsoup4==4.12.2` - HTML parsing
- `lxml==6.0.2` - XML/HTML parser backend
- `apscheduler==3.10.4` - Background job scheduling
- `geopy==2.4.1` - Geocoding service (Nominatim)
- `playwright==1.56.0` - Browser automation for screenshots
- `Pillow==12.0.0` - Image processing for screenshots
- `gunicorn==21.2.0` - WSGI HTTP server for production deployment

### External Services
- **shipnext.com** - Source of ship location data
- **CARTO** - Map tile provider (Positron light style via Leaflet)
- **OpenStreetMap** - Map data source (used by CARTO tiles)
- **Nominatim Geocoding** - Converts location names to coordinates (via Geopy)

## Installation

1. **Install Linux packages**:
```bash
sudo apt-get install libxml2-dev libxslt-dev
sudo apt-get install nodejs
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers** (required for screenshot functionality):
```bash
playwright install chromium
```

4. **Verify installation**:
```bash
python test_destination.py
```

## Running the Application

### Setup Option 1: Single Worker (Simpler, Current Setup)
**Best for:** Low-medium traffic, simple deployment

```bash
# Start Gunicorn with scheduler running in the web worker
gunicorn -c gunicorn.conf.py app:app
```

### Setup Option 2: Multi-Worker (Better for High Traffic)
**Best for:** High traffic, better resource utilization, scalability

```bash
# 1. Modify gunicorn.conf.py: uncomment the multi-worker line
# 2. Use app_no_scheduler.py instead of app.py
# 3. Run scheduler in separate process:
python3 worker.py &

# 4. Run Gunicorn with multiple workers:
gunicorn -c gunicorn.conf.py app_no_scheduler:app
```

**Why separate processes?** Each Gunicorn worker is a separate process with its own memory. The scheduler singleton check only works within one process, so multiple workers would each run their own scheduler, causing duplicate updates.

| Feature | Single Worker (app.py) | Multi-Worker (app_no_scheduler.py + worker.py) |
|---------|----------------------|----------------------------------------------|
| **Workers** | 1 Gunicorn worker | Multiple Gunicorn workers |
| **Scheduler** | Runs in web worker | Runs in separate process |
| **Traffic Capacity** | Low-Medium | High |
| **Setup Complexity** | Simple (1 command) | Moderate (2 processes) |
| **Resource Usage** | Lower | Higher (more workers) |
| **Scalability** | Limited | Better |
| **Best For** | Simple deployments, low traffic | Production, high traffic |

### Development (Flask development server):
```bash
python app.py
```

The application will:
- Initialize the SQLite database (creates `ship_locations.db` if it doesn't exist)
- Start the background scheduler (Option 1) or rely on worker.py (Option 2)
- Run an initial location update
- Take an initial screenshot after 5 seconds (allows server to start)
- Start the server on `http://localhost:3000`

### Access the Application:
- Web interface: `http://localhost:3000`
- API endpoint: `http://localhost:3000/api/location`
- Screenshot: `http://localhost:3000/screenshots/current.bmp`

**Notes**: 
- **Option 1** is simpler but limited to 1 worker (scheduler runs in web worker)
- **Option 2** scales better but requires running worker.py separately
- For development only, you can run with `python app.py` (not recommended for production)

## API Endpoints

All API endpoints are protected by rate limiting. When limits are exceeded, the server returns HTTP 429 (Too Many Requests) with `X-RateLimit-*` headers indicating the limit, remaining requests, and reset time.

### GET /api/location
Returns the latest ship location data.

**Rate Limit**: 120 requests per minute

**Response** (200 OK):
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "timestamp": "2024-01-01T12:00:00",
  "location_text": "New York",
  "speed": 12.5,
  "heading": 45.0,
  "success": true
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "message": "No location data found"
}
```

### GET /api/history
Returns the last 30 location entries.

**Rate Limit**: 120 requests per minute

**Response** (200 OK):
```json
{
  "history": [
    {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "timestamp": "2024-01-01T12:00:00",
      "location_text": "New York",
      "speed": 12.5,
      "heading": 45.0
    },
    ...
  ]
}
```

### POST /api/update
Manually triggers a location update by scraping shipnext.com.

**Rate Limit**: 1 requests per minute (allows customer updates at least once per minute)

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "location_text": "New York",
    "speed": 12.5,
    "heading": 45.0
  }
}
```

**Response** (500 Internal Server Error):
```json
{
  "success": false,
  "message": "Failed to scrape location"
}
```

### GET /screenshots/current.bmp
Serves the latest application screenshot as a BMP image file.

**Rate Limit**: None (exempt from rate limiting)

**Response** (200 OK):
- Returns BMP image file
- Headers include no-cache directives to ensure latest screenshot is served

**Response** (404 Not Found):
- File not found if screenshot hasn't been captured yet

## Configuration

### Gunicorn Settings
Modify `gunicorn.conf.py` to change server configuration:
- **Workers**: Set to 1 to prevent multiple scheduler instances (critical!)
```python
workers = 1  # Do not increase - causes multiple schedulers
```
- **Bind address**: Change host and port
```python
bind = "0.0.0.0:3000"  # Change to desired host:port
```
- **Timeout**: Adjust request timeout
```python
timeout = 30  # Seconds
```
- **Logging**: Configure log levels and output
```python
loglevel = "info"  # Options: debug, info, warning, error, critical
```

**Important**: Always use exactly 1 worker to prevent multiple scheduler instances from running simultaneously, which would cause duplicate updates.

### Update Schedule
Modify `scheduler.py` to change update intervals:
- Ship location updates (around line 80):
```python
hours=6,  # Change to desired hours for location updates
```
- Screenshot updates (around line 90):
```python
hours=1,  # Change to desired hours for screenshot capture
```

### Auto-refresh Interval
Modify `static/app.js` to change frontend refresh interval:
- Location data (around line 228):
```javascript
setInterval(fetchLocation, 5 * 60 * 1000);  // Change milliseconds
```

### Port and Host
Modify `app.py` line 149 to change server configuration:
```python
app.run(host='0.0.0.0', port=3000, debug=True, use_reloader=False)
```

### Database Location
Modify `app.py` line 12 to change database path:
```python
DB_PATH = 'ship_locations.db'  # Change to desired path
```

### API Rate Limiting
Modify `app.py` to adjust rate limits for different endpoints:
```python
# Default limit for all endpoints
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per minute"],  # Change as needed
    storage_uri="memory://",
    strategy="fixed-window"
)

# Specific endpoint limits
@limiter.limit("1 per minute")  # For /api/update endpoint
@limiter.limit("120 per minute")  # For /api/location and /api/history
```

**Current Rate Limits**:
- Default: 200 requests per minute
- `/api/update`: 1 requests per minute (allows customer updates at least once per minute)
- `/api/location` and `/api/history`: 120 requests per minute (read operations)
- Static files and screenshots: Exempt from rate limiting

When rate limits are exceeded, the API returns HTTP 429 (Too Many Requests) with headers indicating the limit and reset time.

### Geocoding Rate Limiting
Modify `scraper.py` line 15 to change geocoding delay:
```python
time.sleep(1)  # Change seconds (rate limiting for Nominatim)
```

## Testing

Run the test suite to verify functionality:
```bash
python test_destination.py
```

**Test Coverage**:
- Scraper functionality (direct scraping test)
- Database operations (table creation, data storage)
- Scheduler update function (end-to-end update test)

## Troubleshooting

### Screenshot Not Accessible
1. Verify Playwright browsers are installed: Run `playwright install chromium`
2. Check if screenshot file exists: Look for `static/screenshots/current.bmp`
3. Check console for screenshot capture errors
4. Ensure the Flask server is accessible at `http://localhost:3000`
5. Wait at least 5 seconds after server start for initial screenshot
6. Try accessing directly: `http://localhost:3000/screenshots/current.bmp`

### No Location Data Displayed
1. Check if scraper is fetching data: Look for debug messages in console
2. Verify database has records: Check `ship_locations.db` file exists
3. Test scraper directly: Run `python test_destination.py`
4. Check network connectivity to shipnext.com

### Scheduler Not Running
1. Check console for scheduler startup messages
2. Verify no duplicate scheduler instances (check for "Scheduler already running" message)
3. Ensure Flask reloader is disabled (`use_reloader=False`)

### Map Not Displaying
1. Check browser console for JavaScript errors
2. Verify Leaflet.js is loading (check Network tab)
3. Ensure API is returning valid coordinate data
4. Check if coordinates are within valid ranges (-90 to 90 for lat, -180 to 180 for lon)
5. Verify CartoDB tile service is accessible (check Network tab for tile requests)
6. If map appears grey, check browser console for CORS or tile loading errors

### Geocoding Failures
1. Nominatim has rate limits - errors are normal and handled gracefully
2. Check internet connectivity
3. Location text may be too ambiguous - check `location_text` in database

### Database Issues
1. Ensure write permissions in application directory
2. Check if database file is locked (close other database connections)
3. Verify SQLite3 is installed on system

### Rate Limiting Issues
1. **HTTP 429 errors**: You've exceeded the rate limit for an endpoint
   - Wait for the rate limit window to reset (shown in `X-RateLimit-Reset` header)
   - Reduce request frequency or adjust limits in `app.py`
2. **Frequent rate limit hits**: Consider increasing limits in the limiter configuration
3. **Multiple clients behind same IP**: All clients share the same rate limit
   - Consider using alternative identification methods (e.g., API keys)
4. **Testing needs**: Temporarily increase limits or use `@limiter.exempt` decorator for specific endpoints

## Data Extraction Details

The scraper uses multiple fallback strategies to extract location data:

1. **Primary Method**: Looks for "Vessel's current position is" text followed by coordinates in DMS or decimal format
2. **HTML Parsing**: Searches for destination-related HTML elements and attributes
3. **Text Patterns**: Uses regex patterns to find destination, speed, and heading information
4. **JavaScript Parsing**: Extracts coordinates from embedded JavaScript/JSON data
5. **Geocoding Fallback**: If coordinates not found but destination text exists, uses Nominatim geocoding

The scraper handles various coordinate formats:
- Decimal degrees: `40.7128, -74.0060`
- DMS format: `40°42'46"N, 74°00'21"W`
- Mixed formats with slashes or commas

## Limitations

- **External Rate Limiting**: shipnext.com may rate-limit requests
- **API Rate Limits**: Application enforces rate limits to prevent abuse (configurable in app.py)
- **HTML Structure Changes**: Scraper may break if shipnext.com changes their HTML structure
- **Geocoding**: Nominatim has usage limits and may fail for ambiguous locations
- **Database**: SQLite may not be suitable for high-traffic scenarios
- **Single Ship**: Currently hardcoded for "Sagittarius Leader" only
- **Screenshot Storage**: Only one screenshot is kept (previous ones are replaced)
- **Screenshot Timing**: 5-second delay after server start may not be sufficient for slow systems

## Features

### History Trail Visualization
The application now displays a visual trail of the ship's recent movements:
- **Last 20 Locations**: Shows the most recent 20 historical positions on the map
- **Black Dot Markers**: Each historical location is represented by a small black dot (8x8 pixels) with a white border
- **Chronological Path**: Dashed black lines connect consecutive historical positions in chronological order (oldest to newest), creating a trail showing where the ship has traveled
- **Toggle Control**: Users can show/hide the entire history trail using a checkbox in the controls panel
- **Auto-Update**: The trail automatically updates when new location data is fetched
- **Visual Clarity**: Lines are semi-transparent (30% opacity) to avoid cluttering the map

**How to Use**:
1. The history trail is visible by default when you load the page
2. Click the "Show History Trail" checkbox in the controls panel to hide/show the trail
3. The trail updates automatically every 5 minutes or when you click "Get Current Location"
4. Historical locations in the sidebar are still clickable to view past positions

## Future Enhancements

Potential improvements:
- Support for multiple ships
- Database migration to PostgreSQL for production
- Redis-backed rate limiting for multi-instance deployments
- API authentication and per-user rate limits
- Caching layer for API responses
- Error notification system
- Export functionality for location data
- Docker containerization
- Environment-based configuration
- Animated route playback feature
- Customizable trail length and styling

## License

[Add license information if applicable]

## Contributing

[Add contribution guidelines if applicable]
