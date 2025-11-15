#!/usr/bin/env python3
"""
Pre-install ChromeDriver using webdriver-manager.
Run this script before starting the application to ensure ChromeDriver is available.
"""

import sys
from datetime import datetime

def install_chromedriver():
    """Install ChromeDriver using webdriver-manager"""
    try:
        print(f"[{datetime.now()}] Installing ChromeDriver...")
        from webdriver_manager.chrome import ChromeDriverManager
        
        driver_path = ChromeDriverManager().install()
        
        if not driver_path or not isinstance(driver_path, str) or not driver_path.strip():
            print(f"[{datetime.now()}] ERROR: ChromeDriverManager returned invalid path: {driver_path}")
            sys.exit(1)
        
        print(f"[{datetime.now()}] SUCCESS: ChromeDriver installed at: {driver_path}")
        return driver_path
        
    except ImportError:
        print(f"[{datetime.now()}] ERROR: webdriver-manager package not found.")
        print(f"[{datetime.now()}] Please install it with: pip install webdriver-manager")
        sys.exit(1)
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: Failed to install ChromeDriver: {e}")
        print(f"[{datetime.now()}] This may indicate:")
        print(f"[{datetime.now()}]   - Network connectivity issues")
        print(f"[{datetime.now()}]   - ChromeDriver download server issues")
        print(f"[{datetime.now()}]   - Permission issues")
        sys.exit(1)

if __name__ == '__main__':
    install_chromedriver()
