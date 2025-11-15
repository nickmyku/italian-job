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
        chrome_options.add_argument('--window-size=1600,960')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')
        
        # Set up ChromeDriver
        # Use webdriver-manager to bypass Selenium Manager issues
        driver = None
        import subprocess
        
        # Check for Chrome binary and set it explicitly if found
        chrome_binary = None
        chrome_found = False
        for chrome_cmd in ['google-chrome', 'chromium-browser', 'chromium']:
            try:
                result = subprocess.run(['which', chrome_cmd], 
                                      capture_output=True, 
                                      timeout=5)
                if result.returncode == 0:
                    chrome_binary = result.stdout.decode().strip()
                    print(f"[{datetime.now()}] Using Chrome binary: {chrome_binary}")
                    chrome_options.binary_location = chrome_binary
                    break
            except Exception:
                continue
        
        # Check Chrome version and extract version number
        chrome_version = None
        for chrome_cmd in ['google-chrome', 'chromium-browser', 'chromium']:
            try:
                result = subprocess.run([chrome_cmd, '--version'], 
                                      capture_output=True, 
                                      timeout=5)
                if result.returncode == 0:
                    chrome_found = True
                    chrome_version_output = result.stdout.decode().strip()
                    print(f"[{datetime.now()}] Found Chrome: {chrome_version_output}")
                    
                    # Extract version number (e.g., "Google Chrome 120.0.6099.109" -> "120.0.6099.109")
                    import re
                    version_match = re.search(r'(\d+\.\d+\.\d+\.\d+|\d+\.\d+\.\d+)', chrome_version_output)
                    if version_match:
                        chrome_version = version_match.group(1)
                        print(f"[{datetime.now()}] Extracted Chrome version: {chrome_version}")
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if not chrome_found:
            print(f"[{datetime.now()}] Chrome browser not found.")
            print(f"[{datetime.now()}] Please install Chrome or Chromium. See README.md Installation section for instructions.")
            raise Exception("Chrome browser not found. Please install Chrome or Chromium.")
        
        # Try to initialize ChromeDriver using webdriver-manager first
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            
            # Get the driver path from ChromeDriverManager
            # Pass version explicitly if we have it to avoid detection issues
            driver_path = None
            if chrome_version:
                # Try multiple version formats to find one that works
                version_attempts = [
                    chrome_version,  # Full version: "120.0.6099.109"
                    chrome_version.split('.')[0],  # Major version: "120"
                    '.'.join(chrome_version.split('.')[:2]),  # Major.minor: "120.0"
                ]
                
                for version_attempt in version_attempts:
                    try:
                        print(f"[{datetime.now()}] Attempting to use ChromeDriverManager with version {version_attempt}...")
                        driver_path = ChromeDriverManager(version=version_attempt).install()
                        if driver_path and isinstance(driver_path, str):
                            print(f"[{datetime.now()}] Successfully got driver path with version {version_attempt}")
                            break
                    except (AttributeError, ValueError, TypeError) as version_error:
                        error_str = str(version_error).lower()
                        # Check if it's the specific split error
                        if "'nonetype' object has no attribute 'split'" in error_str or "nonetype" in error_str:
                            print(f"[{datetime.now()}] Version {version_attempt} failed with split error, trying next version format...")
                            continue
                        else:
                            print(f"[{datetime.now()}] Version {version_attempt} failed: {version_error}, trying next version format...")
                            continue
                
                # If all explicit versions failed, try auto-detection with error handling
                if not driver_path or not isinstance(driver_path, str):
                    print(f"[{datetime.now()}] All explicit versions failed, attempting auto-detection...")
                    try:
                        driver_path = ChromeDriverManager().install()
                    except AttributeError as attr_error:
                        error_str = str(attr_error).lower()
                        # Catch the specific 'NoneType' object has no attribute 'split' error
                        if "'nonetype' object has no attribute 'split'" in error_str or "nonetype" in error_str:
                            print(f"[{datetime.now()}] ChromeDriverManager failed to detect Chrome version. This is a known issue with webdriver-manager.")
                            print(f"[{datetime.now()}] The error occurs when ChromeDriverManager cannot detect Chrome version automatically.")
                            # Re-raise to trigger fallback to Selenium's built-in manager
                            raise AttributeError("ChromeDriverManager version detection failed")
                        else:
                            raise
            else:
                # Auto-detect version
                try:
                    driver_path = ChromeDriverManager().install()
                except AttributeError as attr_error:
                    error_str = str(attr_error).lower()
                    # Catch the specific 'NoneType' object has no attribute 'split' error
                    if "'nonetype' object has no attribute 'split'" in error_str or "nonetype" in error_str:
                        print(f"[{datetime.now()}] ChromeDriverManager failed to detect Chrome version. This is a known issue with webdriver-manager.")
                        print(f"[{datetime.now()}] The error occurs when ChromeDriverManager cannot detect Chrome version automatically.")
                        # Re-raise to trigger fallback to Selenium's built-in manager
                        raise AttributeError("ChromeDriverManager version detection failed")
                    else:
                        raise
            
            if driver_path is None or not isinstance(driver_path, str):
                raise ValueError(f"ChromeDriverManager returned invalid value: {driver_path}")
            
            print(f"[{datetime.now()}] ChromeDriver path: {driver_path}")
            
            # Explicitly use ChromeDriverManager to bypass Selenium Manager
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except ImportError:
            raise Exception("webdriver-manager package is required. Install it with: pip install -r requirements.txt")
        except (AttributeError, ValueError, TypeError) as e:
            error_msg = str(e)
            error_type = type(e).__name__
            print(f"[{datetime.now()}] Error initializing Chrome driver with webdriver-manager ({error_type}): {error_msg}")
            
            # If it's the specific split error, provide more helpful message
            if "'NoneType' object has no attribute 'split'" in error_msg or "nonetype" in error_msg.lower():
                print(f"[{datetime.now()}] ChromeDriverManager could not detect Chrome version. Attempting to use Selenium's built-in driver manager...")
            else:
                print(f"[{datetime.now()}] Attempting to use Selenium's built-in driver manager...")
            
            # Fallback to Selenium's built-in driver manager
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except Exception as fallback_error:
                fallback_error_msg = str(fallback_error)
                print(f"[{datetime.now()}] Error with Selenium's built-in driver manager: {fallback_error_msg}")
                raise Exception(f"Failed to initialize Chrome driver. webdriver-manager error ({error_type}): {error_msg}. Selenium error: {fallback_error_msg}. See README.md for installation instructions.")
        
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
        
        # Take screenshot at 1600x960 (save as PNG first, then convert to BMP)
        print(f"[{datetime.now()}] Capturing screenshot at 1600x960...")
        temp_png_path = os.path.join(SCREENSHOTS_DIR, 'temp_screenshot.png')
        driver.save_screenshot(temp_png_path)
        
        # Convert PNG to BMP and resize to 800x480 resolution
        print(f"[{datetime.now()}] Converting to BMP format and resizing to 800x480...")
        img = Image.open(temp_png_path)
        img_resized = img.resize((800, 480), Image.LANCZOS)
        
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
