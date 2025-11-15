# Ship Tracker - Sagittarius Leader

A web application that scrapes shipnext.com for the destination and location information of the ship "Sagittarius Leader" and displays it on an interactive map with automatic scheduled updates. The application also captures hourly screenshots of itself, accessible at `/screenshots/current.png`.

## Project Overview

This application tracks the location and destination of the cargo ship "Sagittarius Leader" by:
- Scraping real-time data from shipnext.com (vessel page: `https://shipnext.com/vessel/9283887-sagittarius-leader`)
- Storing location history in a SQLite database
- Displaying current location on an interactive map using Leaflet.js
- Providing REST API endpoints for programmatic access
- Automatically updating location data every 6 hours via scheduled background tasks
- **NEW**: Taking hourly screenshots of the application for monitoring, accessible at `/screenshots/current.png`

## Architecture

### Backend (Flask)
- **Framework**: Flask 3.0.0 with CORS enabled
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
│       └── current.png      # Latest application screenshot (created at runtime)
└── README.md                # This file
```

## Component Descriptions

### app.py
Main Flask application that:
- Initializes SQLite database with `ship_locations` table
- Serves static files (HTML, CSS, JS)
- Provides REST API endpoints:
  - `GET /` - Serves index.html
  - `GET /api/location` - Returns latest ship location
  - `GET /api/history` - Returns last 30 location entries
  - `POST /api/update` - Manually triggers location update
  - `GET /screenshots/current.png` - Serves the latest application screenshot
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

### screenshot_util.py
Screenshot capture utility using Playwright:
- **Browser**: Chromium (headless mode)
- **Viewport**: 1920x1080
- **Output**: Saves to `static/screenshots/current.png` (replaces previous screenshot)
- **URL**: Screenshot accessible at `/screenshots/current.png`
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
- Auto-refreshes location data every 5 minutes
- Shows status messages for user feedback

**Key Functions**:
- `initMap()` - Creates Leaflet map instance
- `updateMap(locationData)` - Updates map marker and info panel
- `fetchLocation()` - GET request to `/api/location`
- `manualUpdate()` - POST request to `/api/update`
- `fetchHistory()` - GET request to `/api/history`

### static/index.html
HTML structure with:
- Info panel showing: Last Updated, Destination, Speed, Heading, Coordinates
- Map container (`<div id="map">`)
- History panel with clickable location entries
- Control buttons: "Get Current Location" and "Center Map"
- Status message area

### static/styles.css
CSS styling for the application (not included in file review, but referenced).

## Dependencies

### Python Packages (requirements.txt)
- `flask==3.0.0` - Web framework
- `flask-cors==4.0.0` - CORS support for API
- `requests==2.31.0` - HTTP requests for web scraping
- `beautifulsoup4==4.12.2` - HTML parsing
- `lxml==4.9.3` - XML/HTML parser backend
- `apscheduler==3.10.4` - Background job scheduling
- `geopy==2.4.1` - Geocoding service (Nominatim)
- `playwright==1.40.0` - Browser automation for screenshots

### External Services
- **shipnext.com** - Source of ship location data
- **CARTO** - Map tile provider (Positron light style via Leaflet)
- **OpenStreetMap** - Map data source (used by CARTO tiles)
- **Nominatim Geocoding** - Converts location names to coordinates (via Geopy)

## Installation

1. **Install Linux packages**:
```bash
sudo apt-get install libxml2-dev libxslt-dev
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
- Screenshot: `http://localhost:3000/screenshots/current.png`

**Note**: The Flask server runs with `debug=True` and `use_reloader=False` (reloader disabled to prevent scheduler conflicts).

## API Endpoints

### GET /api/location
Returns the latest ship location data.

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

### GET /screenshots/current.png
Serves the latest application screenshot as a PNG image file.

**Response** (200 OK):
- Returns PNG image file
- Headers include no-cache directives to ensure latest screenshot is served

**Response** (404 Not Found):
- File not found if screenshot hasn't been captured yet

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
2. Check if screenshot file exists: Look for `static/screenshots/current.png`
3. Check console for screenshot capture errors
4. Ensure the Flask server is accessible at `http://localhost:3000`
5. Wait at least 5 seconds after server start for initial screenshot
6. Try accessing directly: `http://localhost:3000/screenshots/current.png`

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

- **Rate Limiting**: shipnext.com may rate-limit requests
- **HTML Structure Changes**: Scraper may break if shipnext.com changes their HTML structure
- **Geocoding**: Nominatim has usage limits and may fail for ambiguous locations
- **Database**: SQLite may not be suitable for high-traffic scenarios
- **Single Ship**: Currently hardcoded for "Sagittarius Leader" only
- **Screenshot Storage**: Only one screenshot is kept (previous ones are replaced)
- **Screenshot Timing**: 5-second delay after server start may not be sufficient for slow systems

## Future Enhancements

Potential improvements:
- Support for multiple ships
- Database migration to PostgreSQL for production
- Caching layer for API responses
- Error notification system
- Historical data visualization (route plotting)
- Export functionality for location data
- Docker containerization
- Environment-based configuration

## License

[Add license information if applicable]

## Contributing

[Add contribution guidelines if applicable]
