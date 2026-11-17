from playwright.sync_api import sync_playwright
import os
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

SCREENSHOT_PATH = 'static/screenshots/current.bmp'
COLOR_SCREENSHOT_PATH = 'static/screenshots/current_color.bmp'

def _to_eink_bw(img):
    """
    Convert an image to high-contrast black-and-white suitable for e-ink.

    Goal: solid black text + country outlines on white land/water. Esri Light
    Gray midtones sit near ~200 after processing — crush them to paper so
    ocean dither noise cannot obscure labels and coasts. Hard 1-bit (no
    dither) keeps strokes solid.
    """
    gray = ImageOps.grayscale(img)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1.2, percent=160, threshold=2))
    # Mild thicken so GeoJSON coasts survive resize
    thickened = gray.filter(ImageFilter.MinFilter(3))
    gray = Image.blend(gray, thickened, 0.22)
    # Darken light-gray Esri reference glyphs toward ink
    gray = gray.point(lambda p: int(round(255 * ((p / 255.0) ** 1.45))))
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.55)

    # Binary ink/paper: midtones become paper so ocean noise cannot hide labels
    return gray.point(lambda p: 0 if p < 150 else 255).convert(
        '1', dither=Image.Dither.NONE
    )

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
            
            # Wait for basemap, label tiles, and country outline GeoJSON
            page.wait_for_timeout(4000)
            try:
                page.wait_for_function(
                    """() => document.querySelectorAll('.leaflet-overlay-pane path').length > 10""",
                    timeout=10000
                )
            except Exception:
                pass
            page.wait_for_timeout(1000)
            
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
