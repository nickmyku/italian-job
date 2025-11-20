# Ship Tracker - Sagittarius Leader

A web application that scrapes shipnext.com for the destination and location information of the ship "Sagittarius Leader" and displays it on an interactive map with automatic scheduled updates. The application also captures hourly screenshots of itself, accessible at `/screenshots/current.bmp`.

## Project Overview

This application tracks the location and destination of the cargo ship "Sagittarius Leader" by:
- Scraping real-time data from shipnext.com (vessel page: `https://shipnext.com/vessel/9283887-sagittarius-leader`)
- Storing location history in a SQLite database
- Displaying current location on an interactive map using Leaflet.js
- Visualizing the last 20 historical locations as a trail on the map with lines connecting chronologically to show the ship's path
- Providing a toggle control to show/hide the history trail
- Displaying origin city and destination information
- Calculating and displaying days until ETA (December 16, 2025)
- Providing REST API endpoints for programmatic access
- Automatically updating location data every 6 hours via scheduled background tasks
- Taking hourly screenshots of the application for monitoring, accessible at `/screenshots/current.bmp` (captured at 1440x960, resized to 960x640)
- Serving robots.txt to block web crawlers

## Architecture

### Backend (Flask)
- **Framework**: Flask 3.0.0 with CORS enabled
- **WSGI Server**: Gunicorn for production deployments
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
3. Parser extracts coordinates, destination text, and origin city
4. Data is stored in SQLite database
5. Frontend requests data via REST API
6. Map displays current location with marker and info panel

## File Structure

```
/workspace/
├── app.py                    # Flask application (main entry point)
├── gunicorn_config.py        # Gunicorn configuration for production
├── scraper.py                # Web scraping logic for shipnext.com
├── scheduler.py              # Background scheduler for automatic updates
├── screenshot_util.py        # Screenshot capture utility using Playwright
├── requirements.txt          # Python dependencies
├── robots.txt                # robots.txt file to block web crawlers
├── test_destination.py       # Test suite for scraper and database
├── ship_locations.db         # SQLite database (created at runtime)
├── static/
│   ├── index.html           # Main HTML page
│   ├── app.js               # Frontend JavaScript (map, API calls)
│   ├── styles.css           # CSS styling
│   ├── favicon.ico          # Favicon
│   └── screenshots/
│       └── current.bmp      # Latest application screenshot (created at runtime)
└── README.md                # This file
```

## Component Descriptions

### app.py
Main Flask application that:
- Initializes SQLite database with `ship_locations` table
- Configures Flask-Limiter for rate limiting API endpoints
- Serves static files (HTML, CSS, JS)
- Provides REST API endpoints:
  - `GET /` - Serves index.html (no rate limit)
  - `GET /robots.txt` - Serves robots.txt file to block web crawlers (no rate limit)
  - `GET /api/location` - Returns latest ship location (120 req/min)
  - `GET /api/history` - Returns last 50 location entries (120 req/min)
  - `POST /api/update` - Manually triggers location update (1 req/min)
  - `GET /screenshots/current.bmp` - Serves the latest application screenshot (no rate limit)
- Starts background scheduler on application startup
- Runs on `0.0.0.0:3000` (accessible on all network interfaces)

**Database Schema** (`ship_locations` table):
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `ship_name` (TEXT) - Currently "Sagittarius Leader"
- `latitude` (REAL) - Decimal degrees (-90 to 90)
- `longitude` (REAL) - Decimal degrees (-180 to 180)
- `timestamp` (TEXT) - ISO format datetime string
- `location_text` (TEXT) - Human-readable destination/port name
- `origin_city` (TEXT) - Origin city/port name (where ship is proceeding from)
- `heading` (REAL) - Reserved for future use (currently NULL)

### scraper.py
Web scraping module that extracts ship location data from shipnext.com:
- **Main Function**: `scrape_ship_location(ship_name)` - Returns dict with location data
- **URL**: `https://shipnext.com/vessel/9283887-sagittarius-leader`
- **Extraction Methods**:
  1. Parses HTML structure using BeautifulSoup
  2. Extracts coordinates from "Vessel's current position is" text pattern
  3. Supports DMS (Degrees/Minutes/Seconds) and decimal degree formats
  4. Extracts destination port name from HTML elements and text patterns
  5. Extracts origin city/port from text patterns (e.g., "from X to Y")
  6. Falls back to geocoding if coordinates not found but destination text exists
- **Return Format**: Dictionary with keys: `latitude`, `longitude`, `location_text`, `origin_city`
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
- Displays ship marker with custom SVG cargo ship icon
- Updates info panel with location details (origin city, destination, ETA, coordinates)
- Calculates and displays days until ETA (December 16, 2025)
- Handles manual updates via button click
- Fetches and displays location history (clickable to view past locations)
- Renders last 20 historical locations as small black dots on the map
- Draws dashed lines connecting historical locations chronologically (oldest to newest) to form a ship trail
- Provides toggle control to show/hide the history trail (enabled by default)
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
- Info panel showing: Last Updated, Origin, Destination, ETA (days until December 16, 2025), Coordinates
- Map container (`<div id="map">`)
- History panel with clickable location entries (collapsible)
- Control buttons: "Get Current Location" and "Center Map"
- Toggle control: Checkbox to show/hide history trail on map (checked by default)
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
- `gunicorn==21.2.0` - WSGI HTTP server for production
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

1. **Setup Virtual Enviornment**:
```bash
python3 -m venv webvenv
source webvenv/bin/activate
``` 

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

### Production Mode (Recommended - Gunicorn):

For production deployments, use Gunicorn: (always use 1 worker option to avoid issues with the scheduler)

```bash
gunicorn --bind 0.0.0.0:3000 --workers 1 --preload app:app
```

**Gunicorn Configuration**:
- Uses `gunicorn_config.py` for production settings
- `--preload` ensures scheduler starts only once in master process
- Worker count is automatically calculated (CPU cores * 2 + 1)
- Logs to stdout/stderr for easy containerization

### Development Mode (Flask Development Server):

For development and testing:

```bash
python app.py
```

The application will:
- Initialize the SQLite database (creates `ship_locations.db` if it doesn't exist)
- Start the background scheduler
- Run an initial location update
- Take an initial screenshot after 5 seconds (allows server to start)
- Start the Flask development server on `http://localhost:3000`

### Access the Application:
- Web interface: `http://localhost:3000`
- API endpoint: `http://localhost:3000/api/location`
- Screenshot: `http://localhost:3000/screenshots/current.bmp`

**Note**: 
- Development server runs with `debug=False` and `use_reloader=False` (reloader disabled to prevent scheduler conflicts)
- For production, always use Gunicorn for better performance and reliability

## HTTPS Configuration

The application supports HTTPS/SSL encryption for secure connections. HTTPS can be enabled by providing SSL certificate files via environment variables.

### Development (Self-Signed Certificates)

For local development and testing, you can generate self-signed certificates:

```bash
# Generate self-signed SSL certificates
./generate_ssl_cert.sh
```

This creates:
- `ssl/cert.pem` - SSL certificate
- `ssl/key.pem` - Private key

Then set environment variables and start Gunicorn:

```bash
export SSL_CERTFILE=ssl/cert.pem
export SSL_KEYFILE=ssl/key.pem
export SSL_PORT=3000
gunicorn --bind 0.0.0.0:3000 --workers 1 --preload app:app
```

Access the application at: `https://localhost:3000`

**Note**: Browsers will show a security warning for self-signed certificates. This is normal for development. Click "Advanced" and "Proceed to localhost" to continue.

### Production (Trusted Certificates)

For production deployments, use certificates from a trusted Certificate Authority (CA), such as Let's Encrypt:

#### Using Let's Encrypt (Certbot)

1. **Install Certbot**:
```bash
sudo apt-get update
sudo apt-get install certbot
```

2. **Obtain certificates** (replace `yourdomain.com` with your domain):
```bash
sudo certbot certonly --standalone -d yourdomain.com
```

3. **Set environment variables**:
```bash
export SSL_CERTFILE=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
export SSL_KEYFILE=/etc/letsencrypt/live/yourdomain.com/privkey.pem
export SSL_PORT=443
```

4. **Start Gunicorn with HTTPS**:
```bash
gunicorn -c gunicorn_config.py --workers 1 app:app
```

5. **Auto-renewal** (recommended):
   - Certificates expire every 90 days
   - Set up a cron job to renew automatically:
```bash
sudo crontab -e
# Add this line:
0 0 * * * certbot renew --quiet && systemctl reload gunicorn
```

#### Using Other Certificate Providers

If you have certificates from another provider:

```bash
export SSL_CERTFILE=/path/to/your/certificate.pem
export SSL_KEYFILE=/path/to/your/private-key.pem
export SSL_PORT=443
gunicorn -c gunicorn_config.py --workers 1 app:app
```

### Environment Variables

- `SSL_CERTFILE` - Path to SSL certificate file (required for HTTPS)
- `SSL_KEYFILE` - Path to SSL private key file (required for HTTPS)
- `SSL_PORT` - Port to bind HTTPS server (default: 3000)

**Important Notes**:
- If `SSL_CERTFILE` and `SSL_KEYFILE` are not set, the server runs in HTTP mode (default behavior)
- Ensure certificate files have appropriate permissions (key file should be readable only by the server user)
- For production, use port 443 (standard HTTPS port) or configure a reverse proxy (nginx/Apache) in front of Gunicorn
- Consider using a reverse proxy (nginx/Apache) in production for additional features like HTTP to HTTPS redirect, load balancing, and static file serving

### Reverse Proxy Setup (Recommended for Production)

For production deployments, it's recommended to use a reverse proxy like nginx in front of Gunicorn:

1. **Gunicorn** runs on localhost with HTTPS (or HTTP)
2. **Nginx** handles:
   - SSL termination (if using nginx SSL)
   - HTTP to HTTPS redirects
   - Static file serving
   - Load balancing (if multiple Gunicorn instances)

Example nginx configuration:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass https://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

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
  "origin_city": "Los Angeles",
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
Returns the last 50 location entries.

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
      "origin_city": "Los Angeles"
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
    "origin_city": "Los Angeles"
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
- Returns BMP image file (960x640 resolution)
- Content-Type: `image/bmp`
- Headers include no-cache directives to ensure latest screenshot is served

**Response** (404 Not Found):
- File not found if screenshot hasn't been captured yet

### GET /robots.txt
Serves the robots.txt file to block web crawlers and search engine bots.

**Rate Limit**: None (exempt from rate limiting)

**Response** (200 OK):
- Returns robots.txt file with Disallow rules for all bots
- Content-Type: `text/plain`

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
3. **Text Patterns**: Uses regex patterns to find destination and origin city information
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
- **ETA Date**: Hardcoded to December 16, 2025 (modify in `static/app.js` to change)
- **Speed/Heading**: Not currently extracted or displayed (fields exist in database but are not populated)

## Features

### Origin and Destination Tracking
- **Origin City**: Displays the port/city the ship is proceeding from
- **Destination**: Shows the current destination port/city
- **Location Text**: Human-readable location information extracted from shipnext.com

### ETA Calculation
- Calculates and displays days until ETA (December 16, 2025)
- Updates automatically as the date approaches
- Shows "Arrived" if the ETA date has passed

### History Trail Visualization
The application displays a visual trail of the ship's recent movements:
- **Last 20 Locations**: Shows the most recent 20 historical positions on the map
- **Black Dot Markers**: Each historical location is represented by a small black dot (10x10 pixels)
- **Chronological Path**: Dashed black lines connect consecutive historical positions in chronological order (oldest to newest), creating a trail showing where the ship has traveled
- **Toggle Control**: Users can show/hide the entire history trail using a checkbox in the controls panel (enabled by default)
- **Auto-Update**: The trail automatically updates when new location data is fetched
- **Visual Clarity**: Lines use dashed pattern with 80% opacity to avoid cluttering the map

**How to Use**:
1. The history trail is visible by default when you load the page
2. Click the "Show History Trail" checkbox in the controls panel to hide/show the trail
3. The trail updates automatically every 5 minutes or when you click "Get Current Location"
4. Historical locations in the sidebar are still clickable to view past positions

### Web Crawler Protection
- Serves `/robots.txt` to block all web crawlers and search engine bots
- Prevents indexing of the application by search engines

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
- Speed and heading extraction from shipnext.com
- Configurable ETA date via API or configuration
- Screenshot history with timestamps

## License

[Add license information if applicable]

## Contributing

[Add contribution guidelines if applicable]
