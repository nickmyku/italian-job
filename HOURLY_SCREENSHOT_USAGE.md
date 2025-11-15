# Hourly Screenshot Script Usage

## Overview
This script (`hourly_screenshot.py`) takes a screenshot of a specified webpage once every hour and overwrites the previous screenshot.

## Features
- ✅ Takes screenshots automatically every hour
- ✅ Overwrites the previous screenshot (single file)
- ✅ Runs continuously in the background
- ✅ Uses headless Chrome browser
- ✅ Configurable URL and output path

## Requirements
All required packages are already in `requirements.txt`:
- selenium
- webdriver-manager
- Pillow (PIL)

## Configuration
Edit these variables in `hourly_screenshot.py`:

```python
WEBPAGE_URL = "http://localhost:3000"  # Change to your target URL
SCREENSHOT_PATH = "hourly_screenshot.png"  # Output file path
SCREENSHOT_INTERVAL = 3600  # 1 hour in seconds
```

## Usage

### Run the script:
```bash
python hourly_screenshot.py
```

### Run in the background (Linux/Mac):
```bash
nohup python hourly_screenshot.py > screenshot.log 2>&1 &
```

### Stop the script:
Press `Ctrl+C` if running in foreground, or kill the process if running in background:
```bash
ps aux | grep hourly_screenshot.py
kill <process_id>
```

## Output
- The script will create/overwrite `hourly_screenshot.png` (or your configured filename) every hour
- Log messages are printed to stdout showing when screenshots are taken
- Each screenshot replaces the previous one, so you always have only the most recent screenshot

## Example Output
```
[2025-11-15 10:00:00.123456] Hourly Screenshot Script Started
Target URL: http://localhost:3000
Output file: hourly_screenshot.png
Interval: 3600 seconds (1.0 hours)
------------------------------------------------------------
[2025-11-15 10:00:00.234567] Taking screenshot of http://localhost:3000...
[2025-11-15 10:00:05.345678] Screenshot saved successfully to hourly_screenshot.png (1234567 bytes)
[2025-11-15 10:00:05.345679] Next screenshot in 3600 seconds...
```

## Notes
- The script takes an initial screenshot immediately when started
- Chrome driver is automatically downloaded/managed by webdriver-manager
- The script runs indefinitely until stopped manually
- Only one screenshot file is kept at a time (overwrites previous)
