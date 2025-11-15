# Screenshot Feature Implementation

## Overview
Added automatic screenshot capture functionality to the Ship Tracker application. The system now takes a screenshot of the web application every hour and makes it accessible at `/screenshots/current.png`.

## Changes Made

### 1. New File: `screenshot_util.py`
- Utilizes Playwright to capture screenshots in headless Chromium browser
- Viewport size: 1920x1080
- Captures full-page screenshots
- Saves to `static/screenshots/current.png` (replaces previous screenshot)
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
- Added new route: `GET /screenshots/<filename>`
- Serves screenshot files directly from `static/screenshots/` folder
- No-cache headers to ensure latest screenshot is always served

### 4. Created: `static/screenshots/` directory
- Houses all screenshot files
- `current.png` is the latest screenshot

### 5. Updated: `requirements.txt`
- Added `playwright==1.40.0` dependency

### 6. Updated: `README.md`
- Documented new screenshot feature
- Added installation instructions for Playwright browsers
- Updated API documentation
- Added troubleshooting section

## How It Works

1. **Scheduler**: Every hour, the background scheduler calls `update_screenshot()`
2. **Screenshot Capture**: Playwright launches a headless Chromium browser, navigates to `http://localhost:3000`, waits for page load, and captures a full-page screenshot
3. **Storage**: Screenshot is saved to `static/screenshots/current.png` (replaces previous one)
4. **Direct Access**: Screenshot is accessible directly at `/screenshots/current.png` via Flask's custom route
5. **No Cache**: Response headers ensure browsers always fetch the latest screenshot

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

### Access the Screenshot
The screenshot is available directly at:
```
http://localhost:3000/screenshots/current.png
```

You can view it in a browser, embed it in other pages, or fetch it programmatically.

### Change Screenshot Resolution
Edit `screenshot_util.py` line 22:
```python
page = browser.new_page(viewport={'width': 1920, 'height': 1080})
```

## Screenshot Endpoint

### GET /screenshots/current.png

**Success Response (200)**:
- Returns PNG image file
- Content-Type: `image/png`
- Cache-Control: `no-cache, no-store, must-revalidate`

**Error Response (404)**:
- File not found if screenshot hasn't been captured yet

### Usage Examples

**In HTML:**
```html
<img src="/screenshots/current.png" alt="Application Screenshot">
```

**Direct Browser Access:**
```
http://localhost:3000/screenshots/current.png
```

**In JavaScript:**
```javascript
fetch('/screenshots/current.png')
  .then(response => response.blob())
  .then(blob => {
    const img = document.createElement('img');
    img.src = URL.createObjectURL(blob);
    document.body.appendChild(img);
  });
```

## Troubleshooting

### Screenshot Not Accessible
1. Wait at least 5 seconds after starting the server
2. Check if Playwright browsers are installed
3. Verify `static/screenshots/current.png` exists
4. Try accessing directly: `http://localhost:3000/screenshots/current.png`
5. Check console logs for errors

### Playwright Installation Issues
If `playwright install chromium` fails:
- Ensure you have sufficient disk space (~200 MB)
- Check internet connectivity
- Try running with sudo if permission errors occur

## Benefits

1. **Monitoring**: Visual verification that the application is running correctly
2. **Direct Access**: Screenshot available as a simple file URL, no API calls needed
3. **Automation**: Fully automated, no manual intervention needed
4. **Minimal Storage**: Only one screenshot stored at a time
5. **Easy Integration**: Can be embedded in external dashboards, monitoring tools, or documentation

## Future Enhancements

Potential improvements:
- Store multiple screenshots with timestamps (screenshot history)
- Configurable screenshot schedule via web UI
- Screenshot comparison to detect UI changes
- Email alerts when screenshots fail
- Multiple viewport sizes (mobile, tablet, desktop)
