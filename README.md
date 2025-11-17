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
├── app.py                    # Flask application (main entry point)
├── scraper.py                # Web scraping logic for shipnext.com
├── scheduler.py              # Background scheduler for automatic updates
├── screenshot_util.py        # Screenshot capture utility using Playwright
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
Main Flask application that:
- Initializes SQLite database with `ship_locations` and `api_keys` tables
- Configures Flask-Limiter for rate limiting API endpoints
- Implements API key authentication for POST endpoints
- Serves static files (HTML, CSS, JS)
- Provides REST API endpoints:
  - `GET /` - Serves index.html (no rate limit)
  - `GET /api/location` - Returns latest ship location (120 req/min)
  - `GET /api/history` - Returns last 30 location entries (120 req/min)
  - `POST /api/update` - Manually triggers location update (60 req/min, **requires API key**)
  - `GET /screenshots/current.bmp` - Serves the latest application screenshot (no rate limit)
- Starts background scheduler on application startup
- Runs on `0.0.0.0:3000` (accessible on all network interfaces)

**Database Schema**:

`ship_locations` table:
- `id` (INTEGER PRIMARY KEY)
- `ship_name` (TEXT) - Currently "Sagittarius Leader"
- `latitude` (REAL) - Decimal degrees (-90 to 90)
- `longitude` (REAL) - Decimal degrees (-180 to 180)
- `timestamp` (TEXT) - ISO format datetime string
- `location_text` (TEXT) - Human-readable destination/port name
- `speed` (REAL) - Speed in knots (optional)
- `heading` (REAL) - Heading in degrees 0-360 (optional)

`api_keys` table:
- `id` (INTEGER PRIMARY KEY)
- `key` (TEXT UNIQUE) - The API key string
- `name` (TEXT) - Descriptive name for the key
- `created_at` (TEXT) - ISO format datetime string
- `last_used` (TEXT) - ISO format datetime string (updated on each use)
- `is_active` (INTEGER) - 1 for active, 0 for disabled

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

### Start the Flask server:
```bash
python app.py
```

The application will:
- Initialize the SQLite database (creates `ship_locations.db` if it doesn't exist)
- Start the background scheduler
- Run an initial location update
- Take an initial screenshot after 5 seconds (allows server to start)
- Start the Flask server on `http://localhost:3000`

### Access the Application:
- Web interface: `http://localhost:3000`
- API endpoint: `http://localhost:3000/api/location`
- Screenshot: `http://localhost:3000/screenshots/current.bmp`

**Note**: The Flask server runs with `debug=True` and `use_reloader=False` (reloader disabled to prevent scheduler conflicts).

## API Endpoints

All API endpoints are protected by rate limiting. When limits are exceeded, the server returns HTTP 429 (Too Many Requests) with `X-RateLimit-*` headers indicating the limit, remaining requests, and reset time.

**Note**: POST endpoints require API key authentication. See the "API Key Authentication" section below for details.

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

**Authentication**: Requires API key (see API Key Authentication section below)

**Rate Limit**: 60 requests per minute (allows customer updates at least once per minute)

**Headers**:
- `X-API-Key`: Your API key (required)

**Example Request**:
```bash
curl -X POST http://localhost:3000/api/update \
  -H "X-API-Key: your-api-key-here"
```

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

**Response** (401 Unauthorized):
```json
{
  "success": false,
  "message": "API key is required. Include it in X-API-Key header or api_key query parameter."
}
```

**Response** (403 Forbidden):
```json
{
  "success": false,
  "message": "Invalid or inactive API key"
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

## API Key Authentication

### Overview

POST endpoints (like `/api/update`) require API key authentication to prevent unauthorized data modifications. GET endpoints remain open for public data access.

### Getting Your API Key

When you first run the application, a default API key is automatically generated and displayed in the console:

```
================================================================================
GENERATED DEFAULT API KEY: your-generated-key-here
Store this key securely! You'll need it to make POST requests.
You can also set a custom key using the API_KEY environment variable.
================================================================================
```

**Important**: Save this key immediately! It's stored in the database but won't be displayed again.

### Setting a Custom API Key

To use a custom API key instead of the auto-generated one, set the `API_KEY` environment variable before running the application:

```bash
export API_KEY="your-custom-api-key"
python app.py
```

### Using API Keys

**In the Web Interface**:
1. Enter your API key in the "API Key" input field
2. Click "Get Current Location" to trigger a manual update
3. The key is stored in your browser's localStorage for convenience

**In API Requests**:

Include the API key in the `X-API-Key` header:

```bash
curl -X POST http://localhost:3000/api/update \
  -H "X-API-Key: your-api-key-here"
```

Or as a query parameter:

```bash
curl -X POST "http://localhost:3000/api/update?api_key=your-api-key-here"
```

### Managing API Keys

API keys are stored in the `api_keys` table in the SQLite database with the following fields:
- `key`: The API key string
- `name`: A descriptive name for the key
- `created_at`: When the key was created
- `last_used`: When the key was last used (updated on each successful authentication)
- `is_active`: Whether the key is active (1) or disabled (0)

To add additional API keys, insert them directly into the database:

```sql
INSERT INTO api_keys (key, name, created_at, is_active)
VALUES ('new-api-key', 'Production Key', datetime('now'), 1);
```

To disable a key without deleting it:

```sql
UPDATE api_keys SET is_active = 0 WHERE key = 'old-api-key';
```

### Security Best Practices

1. **Never commit API keys to version control**
2. **Use environment variables** for production deployments
3. **Rotate keys regularly** by disabling old keys and creating new ones
4. **Use HTTPS** in production to protect keys in transit
5. **Monitor the `last_used` field** to detect unauthorized access

## Configuration

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
@limiter.limit("60 per minute")  # For /api/update endpoint
@limiter.limit("120 per minute")  # For /api/location and /api/history
```

**Current Rate Limits**:
- Default: 200 requests per minute
- `/api/update`: 60 requests per minute (allows customer updates at least once per minute)
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
