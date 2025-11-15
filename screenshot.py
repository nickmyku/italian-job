from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import os
import time
from PIL import Image

SCREENSHOTS_DIR = 'screenshots'
APP_URL = 'http://localhost:3000'

def ensure_screenshots_dir():
    """Create screenshots directory if it doesn't exist"""
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR)
        print(f"[{datetime.now()}] Created screenshots directory: {SCREENSHOTS_DIR}")

def cleanup_old_screenshots():
    """Delete all old screenshots to save memory, keeping only the latest"""
    ensure_screenshots_dir()
    
    if not os.path.exists(SCREENSHOTS_DIR):
        return
    
    deleted_count = 0
    try:
        # Delete all .bmp files in the main screenshots directory (excluding latest/ subdirectory)
        for filename in os.listdir(SCREENSHOTS_DIR):
            filepath = os.path.join(SCREENSHOTS_DIR, filename)
            
            # Skip the 'latest' directory
            if os.path.isdir(filepath) and filename == 'latest':
                continue
            
            # Delete all .bmp files (old timestamped screenshots)
            if filename.endswith('.bmp') and os.path.isfile(filepath):
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    print(f"[{datetime.now()}] Deleted old screenshot: {filename}")
                except Exception as e:
                    print(f"[{datetime.now()}] Warning: Could not delete {filename}: {e}")
        
        if deleted_count > 0:
            print(f"[{datetime.now()}] Cleaned up {deleted_count} old screenshot(s)")
    except Exception as e:
        print(f"[{datetime.now()}] Error during screenshot cleanup: {e}")

def take_screenshot():
    """Take a screenshot of the web app showing ship location"""
    ensure_screenshots_dir()
    
    try:
        print(f"[{datetime.now()}] Starting screenshot capture...")
        
        # Configure Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1280,768')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')
        
        # Set up ChromeDriver
        driver = None
        try:
            # Try to use ChromeDriver from PATH
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"[{datetime.now()}] Warning: Could not initialize Chrome driver: {e}")
            print(f"[{datetime.now()}] Attempting to use ChromeDriverManager...")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except ImportError:
                print(f"[{datetime.now()}] webdriver-manager not available. Please install ChromeDriver manually.")
                raise
            except Exception as e2:
                print(f"[{datetime.now()}] Error with ChromeDriverManager: {e2}")
                raise
        
        if not driver:
            raise Exception("Failed to initialize Chrome driver")
        
        # Navigate to the web app
        print(f"[{datetime.now()}] Navigating to {APP_URL}...")
        driver.get(APP_URL)
        
        # Wait for the map to load (wait for map container or Leaflet tiles)
        print(f"[{datetime.now()}] Waiting for page to load...")
        wait = WebDriverWait(driver, 30)
        
        # Wait for either the map container or some key elements to be present
        try:
            wait.until(EC.presence_of_element_located(("id", "map")))
        except Exception as e:
            print(f"[{datetime.now()}] Warning: Map element not found, proceeding anyway: {e}")
        
        # Additional wait for map tiles to load
        time.sleep(3)
        
        # Clean up old screenshots before taking a new one
        cleanup_old_screenshots()
        
        # Take screenshot at 1280x768 (save as PNG first, then convert to BMP)
        print(f"[{datetime.now()}] Capturing screenshot at 1280x768...")
        temp_png_path = os.path.join(SCREENSHOTS_DIR, 'temp_screenshot.png')
        driver.save_screenshot(temp_png_path)
        
        # Convert PNG to BMP and resize to 1280x768 resolution
        print(f"[{datetime.now()}] Converting to BMP format and resizing to 1280x768...")
        img = Image.open(temp_png_path)
        img_resized = img.resize((1280, 768), Image.LANCZOS)
        
        # Save only to latest/location.bmp (no timestamped version to save memory)
        latest_dir = os.path.join(SCREENSHOTS_DIR, 'latest')
        ensure_screenshots_dir()  # Ensure base directory exists
        if not os.path.exists(latest_dir):
            os.makedirs(latest_dir)
        latest_filepath = os.path.join(latest_dir, 'location.bmp')
        img_resized.save(latest_filepath, 'BMP')
        print(f"[{datetime.now()}] Latest screenshot saved as: {latest_filepath}")
        
        # Remove temporary PNG file
        os.remove(temp_png_path)
        
        # Close the browser
        driver.quit()
        
        return latest_filepath
        
    except Exception as e:
        print(f"[{datetime.now()}] Error taking screenshot: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return None
