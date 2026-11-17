from playwright.sync_api import sync_playwright
import os
from datetime import datetime
from PIL import Image, ImageEnhance, ImageOps

SCREENSHOT_PATH = 'static/screenshots/current.bmp'
COLOR_SCREENSHOT_PATH = 'static/screenshots/current_color.bmp'

def _to_eink_bw(img):
    """
    Convert an image to high-contrast black-and-white suitable for e-ink.
    Uses grayscale + autocontrast + contrast boost, then 1-bit Floyd-Steinberg
    dithering so map detail survives on monochrome displays.
    """
    gray = ImageOps.grayscale(img)
    gray = ImageOps.autocontrast(gray, cutoff=2)
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    return gray.convert('1', dither=Image.Dither.FLOYDSTEINBERG)

def take_screenshot(url='http://localhost:3000'):
    """
    Take a screenshot of the application and save it to static/screenshots folder.
    Saves a color copy as current_color.bmp and a high-contrast B&W e-ink
    version as current.bmp (replaces previous screenshots).
    """
    try:
        print(f"[{datetime.now()}] Taking screenshot of application at {url}...")
        
        # Ensure screenshots directory exists
        os.makedirs(os.path.dirname(SCREENSHOT_PATH), exist_ok=True)
        
        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)
            
            # Create a new page with viewport size at 1440x960
            page = browser.new_page(viewport={'width': 1440, 'height': 960})
            
            # Navigate to the application
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait a bit for map to load
            page.wait_for_timeout(3000)
            
            # Take screenshot to a temporary PNG file first
            temp_path = SCREENSHOT_PATH.replace('.bmp', '_temp.png')
            page.screenshot(path=temp_path, full_page=True)
            
            # Close browser
            browser.close()
        
        # Open the screenshot, resize to 960x640, save color + e-ink BMPs
        with Image.open(temp_path) as img:
            resized_img = img.resize((960, 640), Image.Resampling.LANCZOS)

            # Keep the original color screenshot
            resized_img.save(COLOR_SCREENSHOT_PATH, 'BMP')

            # High-contrast black-and-white for e-ink displays
            eink_img = _to_eink_bw(resized_img)
            eink_img.save(SCREENSHOT_PATH, 'BMP')
        
        # Remove temporary PNG file
        os.remove(temp_path)
            
        print(f"[{datetime.now()}] Color screenshot saved to {COLOR_SCREENSHOT_PATH}")
        print(f"[{datetime.now()}] E-ink B&W screenshot saved to {SCREENSHOT_PATH}")
        print(f"[{datetime.now()}] Screenshot captured at 1440x960, resized to 960x640")
        print(f"[{datetime.now()}] Accessible at: /screenshots/current.bmp and /screenshots/current_color.bmp")
        return True
        
    except Exception as e:
        print(f"[{datetime.now()}] Error taking screenshot: {e}")
        return False

def get_screenshot_path():
    """Get the path to the current e-ink screenshot"""
    if os.path.exists(SCREENSHOT_PATH):
        return SCREENSHOT_PATH
    return None

def get_color_screenshot_path():
    """Get the path to the current color screenshot"""
    if os.path.exists(COLOR_SCREENSHOT_PATH):
        return COLOR_SCREENSHOT_PATH
    return None

def get_screenshot_timestamp():
    """Get the last modified timestamp of the e-ink screenshot"""
    if os.path.exists(SCREENSHOT_PATH):
        return os.path.getmtime(SCREENSHOT_PATH)
    return None
