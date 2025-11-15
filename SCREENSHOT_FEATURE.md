# Screenshot Feature Implementation

## Overview
Added automatic screenshot capture functionality to the Ship Tracker application. The system now takes a screenshot of the web application every hour and makes it accessible at `/screenshots/current.bmp`. Screenshots are captured at 1280x768 resolution, resized to 800x480, and saved in BMP format.

## Changes Made

### 1. New File: `screenshot_util.py`
- Utilizes Playwright to capture screenshots in headless Chromium browser
- Viewport size: 1280x768
- Captures full-page screenshots
- Resizes to 800x480 using PIL/Pillow
- Converts to BMP format
- Saves to `static/screenshots/current.bmp` (replaces previous screenshot)
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
- `current.bmp` is the latest screenshot

### 5. Updated: `requirements.txt`
- Added `playwright==1.40.0` dependency
- Added `Pillow==10.1.0` for image processing (resize and format conversion)

### 6. Updated: `README.md`
- Documented new screenshot feature
- Added installation instructions for Playwright browsers
- Updated API documentation
- Added troubleshooting section

## How It Works

1. **Scheduler**: Every hour, the background scheduler calls `update_screenshot()`
2. **Screenshot Capture**: Playwright launches a headless Chromium browser at 1280x768 resolution, navigates to `http://localhost:3000`, waits for page load, and captures a full-page screenshot
3. **Image Processing**: PIL/Pillow resizes the screenshot from 1280x768 to 800x480
4. **Format Conversion**: The image is converted from PNG to BMP format
5. **Storage**: Screenshot is saved to `static/screenshots/current.bmp` (replaces previous one)
6. **Direct Access**: Screenshot is accessible directly at `/screenshots/current.bmp` via Flask's custom route
7. **No Cache**: Response headers ensure browsers always fetch the latest screenshot

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
http://localhost:3000/screenshots/current.bmp
```

You can view it in a browser, embed it in other pages, or fetch it programmatically.

### Change Screenshot Resolution
Edit `screenshot_util.py` to modify capture resolution (line 24) or output size (line 42):
```python
# Capture resolution
page = browser.new_page(viewport={'width': 1280, 'height': 768})

# Output size
resized_img = img.resize((800, 480), Image.Resampling.LANCZOS)
```

## Screenshot Endpoint

### GET /screenshots/current.bmp

**Success Response (200)**:
- Returns BMP image file (800x480 resolution)
- Content-Type: `image/bmp`
- Cache-Control: `no-cache, no-store, must-revalidate`

**Error Response (404)**:
- File not found if screenshot hasn't been captured yet

### Usage Examples

**In HTML:**
```html
<img src="/screenshots/current.bmp" alt="Application Screenshot">
```

**Direct Browser Access:**
```
http://localhost:3000/screenshots/current.bmp
```

**In JavaScript:**
```javascript
fetch('/screenshots/current.bmp')
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
3. Verify Pillow is installed: `pip install Pillow==10.1.0`
4. Verify `static/screenshots/current.bmp` exists
5. Try accessing directly: `http://localhost:3000/screenshots/current.bmp`
6. Check console logs for errors

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
