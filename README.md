# Ship Tracker - Sagittarius Leader

A web application that scrapes shipnext.com for the destination and location information of the ship "Sagittarius Leader" and displays it on an interactive map with automatic scheduled updates.

## Project Overview

This application tracks the location and destination of the cargo ship "Sagittarius Leader" by:
- Scraping real-time data from shipnext.com (vessel page: `https://shipnext.com/vessel/9283887-sagittarius-leader`)
- Storing location history in a SQLite database
- Displaying current location on an interactive map using Leaflet.js
- Providing REST API endpoints for programmatic access
- Automatically updating location data every 6 hours via scheduled background tasks

## Architecture

### Backend (Flask)
- **Framework**: Flask 3.0.0 with CORS enabled
- **Database**: SQLite (`ship_locations.db`)
- **Scheduler**: APScheduler (BackgroundScheduler) for periodic updates
- **Web Scraping**: BeautifulSoup4 with requests library
- **Geocoding**: Geopy (Nominatim) for converting location names to coordinates

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
├── screenshot.py             # Screenshot capture functionality using Selenium
├── requirements.txt          # Python dependencies
├── test_destination.py      # Test suite for scraper and database
├── ship_locations.db         # SQLite database (created at runtime)
├── screenshots/              # Screenshot output directory (created at runtime)
│   └── latest/              # Latest screenshot subdirectory
│       └── location.bmp     # Latest screenshot (800x480 BMP format)
├── static/
│   ├── index.html           # Main HTML page
│   ├── app.js               # Frontend JavaScript (map, API calls)
│   └── styles.css           # CSS styling
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
  - `GET /api/screenshots` - Lists available screenshots
  - `GET /api/screenshots/<filename>` - Serves a specific screenshot
  - `GET /api/screenshots/latest` - Returns the latest screenshot (BMP)
  - `GET /screenshots/latest/location.bmp` - Direct URL to latest screenshot (BMP)
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
- **Schedule**: Updates every 6 hours (interval-based)
- **Initial Update**: Runs immediately when scheduler starts
- **Singleton Pattern**: Prevents multiple scheduler instances
- **Functions**:
  - `update_ship_location()` - Calls scraper and saves to database
  - Schedules `take_screenshot()` from screenshot.py to run every hour
- **Thread Safety**: Uses ThreadPoolExecutor with non-daemon threads
- **Shutdown**: Registered with `atexit` for graceful shutdown
- **Screenshot Integration**: Automatically takes initial screenshot 5 seconds after startup, then hourly

**Important**: Scheduler runs in background thread, separate from Flask's main thread.

### screenshot.py
Screenshot capture module using Selenium WebDriver:
- **Purpose**: Captures visual screenshots of the web application displaying ship location data
- **Technology**: Selenium WebDriver with Chrome headless browser
- **Configuration**:
  - **Target URL**: `http://localhost:3000` (configured via `APP_URL` constant)
  - **Window Size**: 1600x960 pixels (capture resolution)
  - **Output Size**: 800x480 pixels (final BMP resolution)
  - **Output Format**: BMP (Bitmap)
  - **Output Location**: `screenshots/latest/location.bmp`
  - **Storage Strategy**: Only latest screenshot is kept (old screenshots are automatically deleted)

**Key Functions**:
1. **`ensure_screenshots_dir()`**:
   - Creates `screenshots/` directory if it doesn't exist
   - Creates `screenshots/latest/` subdirectory if needed
   - Returns: None (void function)

2. **`cleanup_old_screenshots()`**:
   - Deletes all old `.bmp` files in the `screenshots/` directory
   - Preserves the `latest/` subdirectory and its contents
   - Prevents disk space accumulation by only keeping the most recent screenshot
   - Returns: None (void function)

3. **`take_screenshot()`**:
   - Main screenshot capture function
   - **Process**:
     1. Checks for Chrome/Chromium browser installation and prints version (informational)
     2. Initializes Chrome WebDriver in headless mode using `webdriver-manager` (primary method)
     3. Falls back to Selenium's built-in driver manager if `webdriver-manager` fails
     4. Navigates to `APP_URL` (http://localhost:3000 by default)
     5. Waits up to 30 seconds for map element (`#map`) to load
     6. Additional 3-second wait for map tiles to render
     7. Calls `cleanup_old_screenshots()` before capture
     8. Captures screenshot at 1600x960 and saves as temporary PNG
     9. Resizes image to 800x480 resolution using PIL/Pillow
     10. Converts PNG to BMP format
     11. Saves final BMP to `screenshots/latest/location.bmp`
     12. Removes temporary PNG file
     13. Closes browser and returns file path
   - **Error Handling**: 
     - Validates ChromeDriverManager returns a valid driver path (not None)
     - Catches and handles `webdriver-manager` errors gracefully
     - Falls back to Selenium's built-in driver manager automatically
     - Returns `None` on failure, prints detailed error messages to console
   - **Returns**: `str` path to saved screenshot file (`screenshots/latest/location.bmp`) or `None` on error

**ChromeDriver Initialization**:
The code uses a two-tier approach for ChromeDriver initialization:
1. **Primary Method**: Uses `webdriver-manager` package to automatically download and manage ChromeDriver
   - Validates that the driver path is not None before use
   - Handles internal `webdriver-manager` errors gracefully
2. **Fallback Method**: If `webdriver-manager` fails, automatically falls back to Selenium's built-in driver manager
   - This ensures the application continues to work even if `webdriver-manager` has issues
   - Selenium 4.15+ includes built-in driver management capabilities

**Dependencies**:
- Selenium WebDriver (Chrome)
- PIL/Pillow (for image processing)
- ChromeDriver (auto-managed via webdriver-manager or Selenium's built-in manager)
- Chrome or Chromium browser (must be installed separately - see Installation section)

**Constants**:
- `SCREENSHOTS_DIR = 'screenshots'` - Output directory name
- `APP_URL = 'http://localhost:3000'` - Web application URL to capture

**Usage Notes**:
- **Requires Chrome/Chromium browser to be installed** (see Installation section)
- ChromeDriver is automatically managed by `webdriver-manager` package (with fallback to Selenium's built-in manager)
- The message "Found Chrome: chromium 142.0.7444.59..." is informational and indicates Chrome was detected successfully
- App must be running on `localhost:3000` before calling `take_screenshot()`
- Screenshot capture is CPU and memory intensive; runs in background via scheduler
- Old screenshots are automatically cleaned up to prevent disk space issues
- The code includes robust error handling for ChromeDriver initialization issues

### static/app.js
Frontend JavaScript that:
- Initializes Leaflet map on page load with CartoDB Positron tiles (minimalist light style)
- Fetches location data from `/api/location`
- Displays ship marker with custom SVG icon
- Updates info panel with location details
- Handles manual updates via button click
- Fetches and displays location history (clickable to view past locations)
- Auto-refreshes every 5 minutes
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
- `selenium` - WebDriver for browser automation (screenshot capture)
- `Pillow` (or `PIL`) - Image processing library for screenshot conversion and resizing
- `webdriver-manager` (optional) - Automatic ChromeDriver management

### External Services
- **shipnext.com** - Source of ship location data
- **CARTO** - Map tile provider (Positron light style via Leaflet)
- **OpenStreetMap** - Map data source (used by CARTO tiles)
- **Nominatim Geocoding** - Converts location names to coordinates (via Geopy)

## Installation

1. **Install Chrome/Chromium browser** (required for screenshot functionality):
   - **Ubuntu/Debian**: See "Screenshot Capture Issues" section in Troubleshooting for installation commands
   - **macOS**: `brew install --cask google-chrome`
   - **Windows**: Download from https://www.google.com/chrome/
   - Verify installation: `google-chrome --version` or `chromium-browser --version`

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Verify installation**:
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
- Create the screenshots directory structure (`screenshots/latest/`)
- Start the background scheduler
- Run an initial location update
- Take an initial screenshot after 5 seconds (allows app to fully load)
- Start the Flask server on `http://localhost:3000`

### Access the Application:
- Web interface: `http://localhost:3000`
- API endpoint: `http://localhost:3000/api/location`

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

### GET /api/screenshots
Lists all available screenshots. Currently only returns the latest screenshot.

**Response** (200 OK):
```json
{
  "screenshots": [
    {
      "filename": "latest/location.bmp",
      "url": "/screenshots/latest/location.bmp",
      "timestamp": "2024-01-01T12:00:00",
      "size": 1152000
    }
  ]
}
```

### GET /api/screenshots/latest
Returns the latest screenshot as a BMP image file.

**Response** (200 OK):
- Content-Type: `image/bmp`
- Body: Binary BMP image data (800x480 pixels)

**Response** (404 Not Found):
```json
{
  "error": "No screenshots available"
}
```

### GET /api/screenshots/<filename>
Serves a specific screenshot file. Currently only supports `latest/location.bmp`, `latest`, or `location.bmp`.

**Response** (200 OK):
- Content-Type: `image/bmp`
- Body: Binary BMP image data

**Response** (404 Not Found):
```json
{
  "error": "Screenshot not found"
}
```

### GET /screenshots/latest/location.bmp
Direct URL endpoint to access the latest screenshot. Provides a simple path for accessing screenshots without API prefix.

**Response** (200 OK):
- Content-Type: `image/bmp`
- Body: Binary BMP image data (800x480 pixels)

**Response** (404 Not Found):
```json
{
  "error": "Latest screenshot not available"
}
```

## Configuration

### Update Schedule
Modify `scheduler.py` line 70 to change update interval:
```python
hours=6,  # Change to desired hours
```

### Screenshot Schedule
Modify `scheduler.py` line 82 to change screenshot capture interval:
```python
hours=1,  # Change to desired hours
```

### Screenshot Output Location
Modify `screenshot.py` line 11 to change screenshots directory:
```python
SCREENSHOTS_DIR = 'screenshots'  # Change to desired directory name
```

### Screenshot Target URL
Modify `screenshot.py` line 12 to change the URL to capture:
```python
APP_URL = 'http://localhost:3000'  # Change to desired URL
```

### Screenshot Resolution
Modify `screenshot.py` line 64 to change capture window size:
```python
chrome_options.add_argument('--window-size=1600,960')  # Change width,height
```

Modify `screenshot.py` line 118 to change output image size:
```python
img_resized = img.resize((800, 480), Image.LANCZOS)  # Change width,height tuple
```

### Auto-refresh Interval
Modify `static/app.js` line 227 to change frontend refresh interval:
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

### Screenshot Capture Issues
1. **ChromeDriver initialization errors**:
   - **"'nonetype' object has not attribute 'slpit'" error**:
     - This error occurs when `webdriver-manager` encounters an internal issue
     - The code now includes automatic fallback to Selenium's built-in driver manager
     - If you see this error, the fallback should activate automatically
     - Check console logs for "Attempting to use Selenium's built-in driver manager..." message
   
   - **ChromeDriver not found / Selenium Manager errors**:
     - **Required**: Install Chrome or Chromium browser on the system
     - **Ubuntu/Debian**: 
       ```bash
       # Option 1: Install Google Chrome
       wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
       echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
       sudo apt-get update
       sudo apt-get install -y google-chrome-stable
       
       # Option 2: Install Chromium (if snap is available)
       sudo snap install chromium
       
       # Option 3: Install Chromium via apt (Debian/Ubuntu)
       sudo apt-get update
       sudo apt-get install -y chromium-browser
       ```
     - **Other Linux distributions**: Install Chrome/Chromium using your package manager
     - **macOS**: `brew install --cask google-chrome`
     - **Windows**: Download and install from https://www.google.com/chrome/
     - The `webdriver-manager` package (already in requirements.txt) will automatically download and manage ChromeDriver
     - **Note**: The code uses `webdriver-manager` as primary method with automatic fallback to Selenium's built-in manager. Ensure Chrome/Chromium is installed before running the application.
   
   - **"Found Chrome: chromium 142.0.7444.59..." message**:
     - This is an **informational message**, not an error
     - It indicates that Chrome/Chromium was successfully detected on the system
     - The application will proceed with driver initialization after this message
     - No action needed if you see this message

2. **Screenshot directory permissions**:
   - Ensure write permissions for `screenshots/` directory
   - Check that application can create subdirectories

3. **Screenshot returns None**:
   - Verify Flask app is running on `http://localhost:3000` before screenshot capture
   - Check console logs for detailed error messages
   - Verify Chrome/Chromium is properly installed
   - Check available disk space (screenshots require ~1MB per image)
   - Review error messages for both `webdriver-manager` and Selenium fallback attempts

4. **Screenshot quality or size issues**:
   - Adjust `--window-size` argument in `screenshot.py` for capture resolution
   - Adjust `resize()` parameters in `screenshot.py` for output resolution
   - BMP format is required for compatibility; conversion happens automatically

5. **Screenshots not updating**:
   - Check scheduler is running (look for "Scheduled job 'take_screenshot'" message)
   - Verify job is executing (check console for screenshot capture messages)
   - Check if old screenshots are being cleaned up properly

6. **Driver initialization troubleshooting**:
   - The code now validates that ChromeDriverManager returns a valid path (not None)
   - If `webdriver-manager` fails, the code automatically attempts Selenium's built-in manager
   - Check console logs for messages indicating which driver manager is being used
   - Both methods should work if Chrome/Chromium is properly installed

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

## Screenshot Functionality Details

### Purpose
The screenshot functionality captures visual representations of the web application's current state, showing the ship location on an interactive map. This is useful for:
- Visual monitoring and status checking
- Integration with external systems that consume image data
- Creating visual logs of ship location history
- Displaying on external displays or dashboards

### How It Works
1. **Scheduled Capture**: The scheduler automatically triggers `take_screenshot()` every hour
2. **Browser Automation**: Selenium WebDriver launches a headless Chrome browser
3. **Page Loading**: Navigates to `http://localhost:3000` and waits for map to fully load
4. **Image Capture**: Takes a screenshot at 1600x960 resolution
5. **Image Processing**: Converts PNG to BMP format and resizes to 800x480
6. **Storage**: Saves to `screenshots/latest/location.bmp` (overwrites previous)
7. **Cleanup**: Deletes old screenshot files to conserve disk space

### File Structure
- **Input**: Web application running at `APP_URL` (default: `http://localhost:3000`)
- **Output**: `screenshots/latest/location.bmp` (single file, always latest)
- **Temporary Files**: `screenshots/temp_screenshot.png` (created and deleted during capture)

### API Access
Screenshots can be accessed via:
- **JSON API**: `GET /api/screenshots` - Returns metadata about available screenshots
- **Direct Access**: `GET /screenshots/latest/location.bmp` - Returns BMP image file
- **API Endpoint**: `GET /api/screenshots/latest` - Returns BMP image file

### Integration Points
- **Scheduler**: `scheduler.py` imports and schedules `take_screenshot()` function
- **Flask App**: `app.py` serves screenshot files via REST API endpoints
- **Directory Management**: `app.py` ensures screenshot directory exists on startup

### Technical Specifications
- **Format**: BMP (Bitmap)
- **Resolution**: 800x480 pixels
- **Capture Resolution**: 1600x960 pixels (before resize)
- **File Size**: Approximately 1.15 MB per screenshot
- **Browser**: Chrome/Chromium headless mode
- **Wait Time**: Up to 30 seconds for page load, plus 3 seconds for map tiles

## Recent Changes

### ChromeDriver Initialization Improvements (Latest)
- **Fixed**: "'nonetype' object has not attribute 'slpit'" error handling
  - Added validation to ensure ChromeDriverManager returns a valid driver path
  - Implemented automatic fallback to Selenium's built-in driver manager
  - Improved error messages for better troubleshooting
- **Clarified**: "Found Chrome: chromium..." message is informational, not an error
- **Enhanced**: Error handling now provides detailed messages for both primary and fallback driver initialization methods

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
- Screenshot format options (PNG, JPEG) in addition to BMP
- Screenshot history with timestamped files
- Screenshot capture on demand via API endpoint

## License

[Add license information if applicable]

## Contributing

[Add contribution guidelines if applicable]
