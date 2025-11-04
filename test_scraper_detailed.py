#!/usr/bin/env python3
"""
Comprehensive test script to verify speed and heading extraction from shipnext.com
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from scraper import scrape_ship_location

def test_scraper():
    """Test the main scraper function"""
    print("=" * 80)
    print("TEST 1: Testing main scraper function")
    print("=" * 80)
    
    result = scrape_ship_location('Sagittarius Leader')
    
    print("\nScraper Results:")
    print(json.dumps(result, indent=2, default=str))
    
    print("\n✓ Speed:", result.get('speed') if result else None)
    print("✓ Heading:", result.get('heading') if result else None)
    
    if result:
        speed_found = result.get('speed') is not None
        heading_found = result.get('heading') is not None
        print(f"\n{'✓' if speed_found else '✗'} Speed extraction: {'SUCCESS' if speed_found else 'FAILED - value is None'}")
        print(f"{'✓' if heading_found else '✗'} Heading extraction: {'SUCCESS' if heading_found else 'FAILED - value is None'}")
    else:
        print("\n✗ Scraper returned None")
    
    return result

def test_direct_html_extraction():
    """Test direct HTML extraction"""
    print("\n" + "=" * 80)
    print("TEST 2: Direct HTML extraction test")
    print("=" * 80)
    
    vessel_url = "https://shipnext.com/vessel/9283887-sagittarius-leader"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print("Fetching page...")
    response = requests.get(vessel_url, headers=headers, timeout=30)
    response.encoding = response.apparent_encoding or 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    text_content = soup.get_text()
    response_text = response.text
    
    print(f"Response length: {len(response_text)} chars")
    print(f"Parsed text length: {len(text_content)} chars")
    
    # Test speed extraction
    print("\n--- Testing Speed Extraction ---")
    speed_patterns = [
        r'Speed[:\s]+([\d.]+)\s*(?:knots?|kn|kts)?',
        r'SOG[:\s]+([\d.]+)',
        r'speed["\']?\s*[:=]\s*([\d.]+)',
        r'"speed"\s*:\s*(\d+\.?\d*)',
    ]
    
    speed_found = False
    for pattern in speed_patterns:
        matches = re.findall(pattern, text_content, re.I)
        if matches:
            print(f"  ✓ Found with pattern '{pattern[:50]}...': {matches[:3]}")
            speed_found = True
        else:
            # Also check raw HTML
            matches = re.findall(pattern, response_text, re.I)
            if matches:
                print(f"  ✓ Found in raw HTML with pattern '{pattern[:50]}...': {matches[:3]}")
                speed_found = True
    
    if not speed_found:
        print("  ✗ No speed values found in HTML")
    
    # Test heading extraction
    print("\n--- Testing Heading Extraction ---")
    heading_patterns = [
        r'Heading[:\s]+([\d.]+)\s*(?:°|deg|degrees)?',
        r'COG[:\s]+([\d.]+)\s*(?:°|deg|degrees)?',
        r'Course[:\s]+([\d.]+)\s*(?:°|deg|degrees)?',
        r'heading["\']?\s*[:=]\s*([\d.]+)',
        r'"heading"\s*:\s*(\d+\.?\d*)',
    ]
    
    heading_found = False
    for pattern in heading_patterns:
        matches = re.findall(pattern, text_content, re.I)
        if matches:
            print(f"  ✓ Found with pattern '{pattern[:50]}...': {matches[:3]}")
            heading_found = True
        else:
            # Also check raw HTML
            matches = re.findall(pattern, response_text, re.I)
            if matches:
                print(f"  ✓ Found in raw HTML with pattern '{pattern[:50]}...': {matches[:3]}")
                heading_found = True
    
    if not heading_found:
        print("  ✗ No heading values found in HTML")
    
    # Test table extraction
    print("\n--- Testing Table Extraction ---")
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    
    for i, table in enumerate(tables[:3]):  # Check first 3 tables
        rows = table.find_all('tr')
        print(f"  Table {i+1}: {len(rows)} rows")
        for row in rows[:5]:  # Check first 5 rows
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if any(kw in label.lower() for kw in ['speed', 'heading', 'course', 'sog', 'cog']):
                    print(f"    Found: {label} = {value}")
    
    return speed_found or heading_found

def test_javascript_data():
    """Test JavaScript/JSON data extraction"""
    print("\n" + "=" * 80)
    print("TEST 3: JavaScript/JSON data extraction")
    print("=" * 80)
    
    vessel_url = "https://shipnext.com/vessel/9283887-sagittarius-leader"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(vessel_url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    scripts = soup.find_all('script')
    
    print(f"Found {len(scripts)} script tags")
    
    found_data = False
    for i, script in enumerate(scripts):
        if script.string:
            script_text = script.string
            
            # Look for JSON objects with speed/heading
            json_patterns = [
                (r'"speed"\s*:\s*(\d+\.?\d*)', 'speed'),
                (r'"heading"\s*:\s*(\d+\.?\d*)', 'heading'),
                (r'"course"\s*:\s*(\d+\.?\d*)', 'course'),
                (r'speed["\']?\s*[:=]\s*(\d+\.?\d*)', 'speed (alt)'),
                (r'heading["\']?\s*[:=]\s*(\d+\.?\d*)', 'heading (alt)'),
            ]
            
            for pattern, name in json_patterns:
                matches = re.findall(pattern, script_text, re.I)
                if matches:
                    print(f"  ✓ Script {i}: Found {name}: {matches[:3]}")
                    found_data = True
    
    if not found_data:
        print("  ✗ No speed/heading found in JavaScript")
    
    return found_data

def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE SCRAPER TEST")
    print("=" * 80)
    
    # Test 1: Main scraper
    result = test_scraper()
    
    # Test 2: Direct HTML extraction
    html_found = test_direct_html_extraction()
    
    # Test 3: JavaScript data
    js_found = test_javascript_data()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    if result:
        speed_ok = result.get('speed') is not None
        heading_ok = result.get('heading') is not None
        print(f"Scraper Speed: {'✓ FOUND' if speed_ok else '✗ NOT FOUND (None)'}")
        print(f"Scraper Heading: {'✓ FOUND' if heading_ok else '✗ NOT FOUND (None)'}")
    else:
        print("Scraper: ✗ Returned None")
    
    print(f"HTML Extraction: {'✓ Data found' if html_found else '✗ No data found'}")
    print(f"JavaScript Extraction: {'✓ Data found' if js_found else '✗ No data found'}")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    
    if result and result.get('speed') is not None and result.get('heading') is not None:
        print("✓ SUCCESS: Scraper is extracting speed and heading values!")
    else:
        print("✗ FAILURE: Scraper cannot extract speed/heading from the website.")
        print("  Reason: Data is not present in static HTML - likely loaded dynamically via JavaScript.")
        print("  Recommendation: Use a headless browser (Selenium/Playwright) to execute JavaScript.")

if __name__ == '__main__':
    main()
