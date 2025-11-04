from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime
from scraper import scrape_ship_location
import sqlite3
import atexit

DB_PATH = 'ship_locations.db'

# Global scheduler instance
_scheduler = None

def update_ship_location():
    """Update ship location in database"""
    print(f"[{datetime.now()}] Updating ship location...")
    try:
        location_data = scrape_ship_location('Sagittarius Leader')
        # Save if we have coordinates OR destination text
        if location_data and (location_data.get('latitude') or location_data.get('location_text')):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('''
                INSERT INTO ship_locations 
                (ship_name, latitude, longitude, timestamp, location_text, speed, heading)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'Sagittarius Leader',
                location_data.get('latitude'),
                location_data.get('longitude'),
                datetime.now().isoformat(),
                location_data.get('location_text', ''),
                location_data.get('speed'),
                location_data.get('heading')
            ))
            conn.commit()
            conn.close()
            coord_info = f"{location_data.get('latitude')}, {location_data.get('longitude')}" if location_data.get('latitude') else "No coordinates"
            dest_info = f", Destination: {location_data.get('location_text')}" if location_data.get('location_text') else ""
            speed_info = f", Speed: {location_data.get('speed')}" if location_data.get('speed') else ""
            heading_info = f", Heading: {location_data.get('heading')}" if location_data.get('heading') else ""
            print(f"[{datetime.now()}] Location updated successfully: {coord_info}{dest_info}{speed_info}{heading_info}")
        else:
            print(f"[{datetime.now()}] Failed to retrieve location data (no coordinates or destination)")
    except Exception as e:
        print(f"[{datetime.now()}] Error updating location: {e}")

def start_scheduler():
    """Start the background scheduler for updates every 6 hours"""
    global _scheduler
    
    # Prevent multiple scheduler instances (important for Flask reloader)
    if _scheduler is not None and _scheduler.running:
        print("Scheduler already running. Skipping start.")
        return _scheduler
    
    # Configure executor with non-daemon threads to prevent premature termination
    executors = {
        'default': ThreadPoolExecutor(1)
    }
    
    # Create scheduler with explicit configuration
    _scheduler = BackgroundScheduler(executors=executors)
    
    # Check if job already exists to prevent duplicates
    if not _scheduler.get_job('ship_update'):
        # Schedule update every 6 hours
        _scheduler.add_job(
            update_ship_location,
            'interval',
            hours=6,
            id='ship_update',
            replace_existing=True
        )
        print(f"[{datetime.now()}] Scheduled job 'ship_update' to run every 6 hours.")
    
    # Start scheduler
    if not _scheduler.running:
        _scheduler.start()
        print(f"[{datetime.now()}] Scheduler started. Updates scheduled every 6 hours.")
        
        # Print next run time
        job = _scheduler.get_job('ship_update')
        if job:
            next_run = job.next_run_time
            print(f"[{datetime.now()}] Next scheduled update: {next_run}")
        
        # Register shutdown handler
        atexit.register(lambda: _scheduler.shutdown() if _scheduler else None)
    
    # Run initial update
    print(f"[{datetime.now()}] Running initial update...")
    update_ship_location()
    
    return _scheduler
