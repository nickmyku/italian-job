from playwright.sync_api import sync_playwright
import os
from datetime import datetime

SCREENSHOT_PATH = 'static/screenshots/current.png'

def take_screenshot(url='http://localhost:3000'):
    """
    Take a screenshot of the application and save it to static/screenshots folder
    Replaces the previous screenshot
    """
    try:
        print(f"[{datetime.now()}] Taking screenshot of application at {url}...")
        
        # Ensure screenshots directory exists
        os.makedirs(os.path.dirname(SCREENSHOT_PATH), exist_ok=True)
        
        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)
            
            # Create a new page with viewport size
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            # Navigate to the application
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait a bit for map to load
            page.wait_for_timeout(3000)
            
            # Take screenshot and save it (replaces previous one)
            page.screenshot(path=SCREENSHOT_PATH, full_page=True)
            
            # Close browser
            browser.close()
            
        print(f"[{datetime.now()}] Screenshot saved successfully to {SCREENSHOT_PATH}")
        print(f"[{datetime.now()}] Screenshot accessible at: /screenshots/current.png")
        return True
        
    except Exception as e:
        print(f"[{datetime.now()}] Error taking screenshot: {e}")
        return False

def get_screenshot_path():
    """Get the path to the current screenshot"""
    if os.path.exists(SCREENSHOT_PATH):
        return SCREENSHOT_PATH
    return None

def get_screenshot_timestamp():
    """Get the last modified timestamp of the screenshot"""
    if os.path.exists(SCREENSHOT_PATH):
        return os.path.getmtime(SCREENSHOT_PATH)
    return None
