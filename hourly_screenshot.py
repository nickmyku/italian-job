#!/usr/bin/env python3
"""
Hourly Screenshot Script
Takes a screenshot of a specified webpage once every hour and overwrites the previous screenshot.
"""

import os
import time
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
WEBPAGE_URL = "http://localhost:3000"  # Change this to your target webpage URL
SCREENSHOT_PATH = "hourly_screenshot.png"  # Output file path (will be overwritten each hour)
SCREENSHOT_INTERVAL = 3600  # 1 hour in seconds

# Global flag to control the screenshot loop
_screenshot_running = False
_screenshot_thread = None

def take_screenshot():
    """Take a screenshot of the webpage and save it, overwriting any existing file."""
    try:
        print(f"[{datetime.now()}] Taking screenshot of {WEBPAGE_URL}...")
        
        # Setup Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Initialize Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Navigate to the webpage
        driver.get(WEBPAGE_URL)
        
        # Wait for page to load
        time.sleep(3)
        
        # Take screenshot and save it (overwriting any existing file)
        driver.save_screenshot(SCREENSHOT_PATH)
        
        # Close the browser
        driver.quit()
        
        # Get file size for confirmation
        file_size = os.path.getsize(SCREENSHOT_PATH) if os.path.exists(SCREENSHOT_PATH) else 0
        
        print(f"[{datetime.now()}] Screenshot saved successfully to {SCREENSHOT_PATH} ({file_size} bytes)")
        
    except Exception as e:
        print(f"[{datetime.now()}] Error taking screenshot: {e}")

def _screenshot_loop():
    """Internal loop that takes screenshots every hour."""
    global _screenshot_running
    
    print(f"[{datetime.now()}] Hourly Screenshot Loop Started")
    print(f"Target URL: {WEBPAGE_URL}")
    print(f"Output file: {SCREENSHOT_PATH}")
    print(f"Interval: {SCREENSHOT_INTERVAL} seconds ({SCREENSHOT_INTERVAL/3600} hours)")
    print("-" * 60)
    
    # Wait a few seconds before taking first screenshot to let server fully start
    time.sleep(5)
    
    # Take initial screenshot
    take_screenshot()
    
    # Continue taking screenshots every hour
    while _screenshot_running:
        try:
            # Wait for the specified interval
            print(f"[{datetime.now()}] Next screenshot in {SCREENSHOT_INTERVAL} seconds...")
            time.sleep(SCREENSHOT_INTERVAL)
            
            # Check if still running (in case stopped during sleep)
            if _screenshot_running:
                take_screenshot()
            
        except Exception as e:
            print(f"[{datetime.now()}] Unexpected error in screenshot loop: {e}")
            if _screenshot_running:
                print(f"[{datetime.now()}] Retrying in {SCREENSHOT_INTERVAL} seconds...")
                time.sleep(SCREENSHOT_INTERVAL)

def start_screenshot_service():
    """Start the screenshot service in a background thread."""
    global _screenshot_running, _screenshot_thread
    
    # Prevent multiple instances
    if _screenshot_running:
        print("Screenshot service already running. Skipping start.")
        return
    
    _screenshot_running = True
    _screenshot_thread = threading.Thread(target=_screenshot_loop, daemon=True, name="ScreenshotThread")
    _screenshot_thread.start()
    print(f"[{datetime.now()}] Screenshot service started in background thread")

def stop_screenshot_service():
    """Stop the screenshot service."""
    global _screenshot_running
    
    if _screenshot_running:
        print(f"[{datetime.now()}] Stopping screenshot service...")
        _screenshot_running = False

def main():
    """Main function for standalone execution."""
    start_screenshot_service()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Script stopped by user")
        stop_screenshot_service()

if __name__ == "__main__":
    main()
