# Screenshot Feature Implementation

## Overview
Added automatic screenshot capture functionality to the Ship Tracker application. The system now takes a screenshot of the web application every hour and displays it in the web interface.

## Changes Made

### 1. New File: `screenshot_util.py`
- Utilizes Playwright to capture screenshots in headless Chromium browser
- Viewport size: 1920x1080
- Captures full-page screenshots
- Saves to `static/screenshot.png` (replaces previous screenshot)
- Functions:
  - `take_screenshot(url)` - Captures screenshot
  - `get_screenshot_path()` - Returns screenshot file path
  - `get_screenshot_timestamp()` - Returns last modified time

### 2. Updated: `scheduler.py`
- Added `update_screenshot()` function
- Scheduled screenshot capture every 1 hour
- Initial screenshot taken 5 seconds after server starts
- Integrated with existing APScheduler background jobs

### 3. Updated: `app.py`
- Added new API endpoint: `GET /api/screenshot`
- Returns screenshot metadata (path, timestamp)
- Imports screenshot utility functions

### 4. Updated: `static/index.html`
- Added screenshot panel section
- Displays screenshot image with timestamp
- Placeholder shown when screenshot not available

### 5. Updated: `static/styles.css`
- Styled screenshot panel with modern look
- Responsive screenshot container
- Placeholder styling for loading/error states

### 6. Updated: `static/app.js`
- Added `fetchScreenshot()` function
- Auto-refreshes screenshot every 2 minutes
- Handles screenshot loading and error states
- Cache-busting to ensure latest screenshot is shown

### 7. Updated: `requirements.txt`
- Added `playwright==1.40.0` dependency

### 8. Updated: `README.md`
- Documented new screenshot feature
- Added installation instructions for Playwright browsers
- Updated API documentation
- Added troubleshooting section

## How It Works

1. **Scheduler**: Every hour, the background scheduler calls `update_screenshot()`
2. **Screenshot Capture**: Playwright launches a headless Chromium browser, navigates to `http://localhost:3000`, waits for page load, and captures a full-page screenshot
3. **Storage**: Screenshot is saved to `static/screenshot.png` (replaces previous one)
4. **Web Display**: Frontend fetches screenshot metadata via `/api/screenshot` endpoint and displays the image
5. **Auto-Refresh**: Screenshot display refreshes every 2 minutes to show new captures

## Installation Requirements

After pulling the code, users need to:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (IMPORTANT!)
playwright install chromium
```

## Configuration

### Change Screenshot Frequency
Edit `scheduler.py` around line 90:
```python
hours=1,  # Change to desired hours
```

### Change Display Refresh Rate
Edit `static/app.js` around line 266:
```javascript
setInterval(fetchScreenshot, 2 * 60 * 1000);  // Change milliseconds
```

### Change Screenshot Resolution
Edit `screenshot_util.py` line 22:
```python
page = browser.new_page(viewport={'width': 1920, 'height': 1080})
```

## API Endpoint

### GET /api/screenshot

**Success Response (200)**:
```json
{
  "success": true,
  "path": "/static/screenshot.png",
  "timestamp": 1704110400.123,
  "last_updated": "2024-01-01T12:00:00"
}
```

**Error Response (404)**:
```json
{
  "success": false,
  "message": "No screenshot available yet"
}
```

## Troubleshooting

### Screenshot Not Appearing
1. Wait at least 5 seconds after starting the server
2. Check if Playwright browsers are installed
3. Verify `static/screenshot.png` exists
4. Check console logs for errors

### Playwright Installation Issues
If `playwright install chromium` fails:
- Ensure you have sufficient disk space (~200 MB)
- Check internet connectivity
- Try running with sudo if permission errors occur

## Benefits

1. **Monitoring**: Visual verification that the application is running correctly
2. **Debugging**: Historical view of UI state
3. **Automation**: Fully automated, no manual intervention needed
4. **Minimal Storage**: Only one screenshot stored at a time

## Future Enhancements

Potential improvements:
- Store multiple screenshots with timestamps (screenshot history)
- Configurable screenshot schedule via web UI
- Screenshot comparison to detect UI changes
- Email alerts when screenshots fail
- Multiple viewport sizes (mobile, tablet, desktop)
