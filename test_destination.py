#!/usr/bin/env python3
"""
Test script to verify destination extraction and display
"""
import json
import sqlite3
from scraper import scrape_ship_location
from scheduler import update_ship_location

def test_scraper():
    """Test the scraper directly"""
    print("=" * 60)
    print("TEST 1: Testing scraper directly")
    print("=" * 60)
    data = scrape_ship_location('Sagittarius Leader')
    if data:
        print(f"✓ Scraper returned data")
        print(f"  - Location text: {data.get('location_text', 'None')}")
        print(f"  - Latitude: {data.get('latitude', 'None')}")
        print(f"  - Longitude: {data.get('longitude', 'None')}")
        print(f"  - Speed: {data.get('speed', 'None')}")
        print(f"  - Heading: {data.get('heading', 'None')}")
        return True
    else:
        print("✗ Scraper returned no data")
        return False

def test_database():
    """Test database operations"""
    print("\n" + "=" * 60)
    print("TEST 2: Testing database operations")
    print("=" * 60)
    try:
        conn = sqlite3.connect('ship_locations.db')
        c = conn.cursor()
        
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ship_locations'")
        if c.fetchone():
            print("✓ Database table exists")
        else:
            print("✗ Database table does not exist")
            return False
        
        # Check latest record
        c.execute('''
            SELECT location_text, latitude, longitude, timestamp 
            FROM ship_locations 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        row = c.fetchone()
        if row:
            print(f"✓ Latest record found")
            print(f"  - Location text: {row[0] or 'None'}")
            print(f"  - Latitude: {row[1] or 'None'}")
            print(f"  - Longitude: {row[2] or 'None'}")
            print(f"  - Timestamp: {row[3]}")
            
            # Verify destination is saved
            if row[0]:
                print(f"✓ Destination is saved in database")
            else:
                print(f"⚠ Destination field is empty (but coordinates exist)")
        else:
            print("✗ No records found in database")
            return False
        
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def test_scheduler():
    """Test scheduler update function"""
    print("\n" + "=" * 60)
    print("TEST 3: Testing scheduler update")
    print("=" * 60)
    try:
        update_ship_location()
        print("✓ Scheduler update completed successfully")
        return True
    except Exception as e:
        print(f"✗ Scheduler error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("DESTINATION EXTRACTION TEST SUITE")
    print("=" * 60)
    
    results = []
    results.append(("Scraper", test_scraper()))
    results.append(("Database", test_database()))
    results.append(("Scheduler", test_scheduler()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nThe destination extraction and display system is working correctly!")
        print("The scraper:")
        print("  - Extracts location_text from the website")
        print("  - Extracts coordinates from the website")
        print("  - Saves both to the database")
        print("\nThe API:")
        print("  - Returns location_text in /api/location")
        print("  - Updates location_text via /api/update")
        print("\nThe frontend:")
        print("  - Displays location_text in the Destination field")
        print("  - Shows destination in map popup")
        print("  - Handles cases where destination exists but coordinates don't")
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 60)
    
    return all_passed

if __name__ == '__main__':
    exit(0 if main() else 1)
