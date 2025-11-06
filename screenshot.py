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
        chrome_options.add_argument('--window-size=1280,720')
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
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ship_location_{timestamp}.bmp'
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        
        # Take screenshot at 1280x720 (save as PNG first, then convert to BMP)
        print(f"[{datetime.now()}] Capturing screenshot at 1280x720...")
        temp_png_path = filepath.replace('.bmp', '_temp.png')
        driver.save_screenshot(temp_png_path)
        
        # Convert PNG to BMP and resize to 800x480 resolution
        print(f"[{datetime.now()}] Converting to BMP format and resizing to 800x480...")
        img = Image.open(temp_png_path)
        img_resized = img.resize((800, 480), Image.LANCZOS)
        img_resized.save(filepath, 'BMP')
        
        # Remove temporary PNG file
        os.remove(temp_png_path)
        
        print(f"[{datetime.now()}] Screenshot saved as BMP: {filepath}")
        
        # Close the browser
        driver.quit()
        
        return filepath
        
    except Exception as e:
        print(f"[{datetime.now()}] Error taking screenshot: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return None
