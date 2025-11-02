from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from scraper import scrape_ship_location
import sqlite3

DB_PATH = 'ship_locations.db'

def update_ship_location():
    """Update ship location in database"""
    print(f"[{datetime.now()}] Updating ship location...")
    try:
        location_data = scrape_ship_location('Sagittarius Leader')
        if location_data and location_data.get('latitude'):
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
            print(f"[{datetime.now()}] Location updated successfully: {location_data.get('latitude')}, {location_data.get('longitude')}")
        else:
            print(f"[{datetime.now()}] Failed to retrieve location data")
    except Exception as e:
        print(f"[{datetime.now()}] Error updating location: {e}")

def start_scheduler():
    """Start the background scheduler for daily updates"""
    scheduler = BackgroundScheduler()
    # Schedule update daily at 00:00 UTC (adjust timezone as needed)
    scheduler.add_job(
        update_ship_location,
        'cron',
        hour=0,
        minute=0,
        id='daily_ship_update'
    )
    scheduler.start()
    print("Scheduler started. Daily updates scheduled for 00:00 UTC.")
    
    # Run initial update
    update_ship_location()
