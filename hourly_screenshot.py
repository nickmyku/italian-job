#!/usr/bin/env python3
"""
Hourly Screenshot Script
Takes a screenshot of a specified webpage once every hour and overwrites the previous screenshot.
"""

import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
WEBPAGE_URL = "http://localhost:3000"  # Change this to your target webpage URL
SCREENSHOT_PATH = "hourly_screenshot.png"  # Output file path (will be overwritten each hour)
SCREENSHOT_INTERVAL = 3600  # 1 hour in seconds

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

def main():
    """Main loop that takes screenshots every hour."""
    print(f"[{datetime.now()}] Hourly Screenshot Script Started")
    print(f"Target URL: {WEBPAGE_URL}")
    print(f"Output file: {SCREENSHOT_PATH}")
    print(f"Interval: {SCREENSHOT_INTERVAL} seconds ({SCREENSHOT_INTERVAL/3600} hours)")
    print("-" * 60)
    
    # Take initial screenshot immediately
    take_screenshot()
    
    # Continue taking screenshots every hour
    while True:
        try:
            # Wait for the specified interval
            print(f"[{datetime.now()}] Next screenshot in {SCREENSHOT_INTERVAL} seconds...")
            time.sleep(SCREENSHOT_INTERVAL)
            
            # Take screenshot
            take_screenshot()
            
        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] Script stopped by user")
            break
        except Exception as e:
            print(f"[{datetime.now()}] Unexpected error: {e}")
            print(f"[{datetime.now()}] Retrying in {SCREENSHOT_INTERVAL} seconds...")
            time.sleep(SCREENSHOT_INTERVAL)

if __name__ == "__main__":
    main()
