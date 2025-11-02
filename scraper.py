import requests
from bs4 import BeautifulSoup
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

def geocode_location(location_text):
    """Convert location text to coordinates"""
    if not location_text:
        return None, None
    
    geolocator = Nominatim(user_agent="ship_tracker")
    try:
        time.sleep(1)  # Rate limiting
        location = geolocator.geocode(location_text, timeout=10)
        if location:
            return location.latitude, location.longitude
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Geocoding error: {e}")
    return None, None

def extract_coordinates_from_text(text):
    """Try to extract coordinates directly from text"""
    if not text:
        return None, None
    
    # Look for patterns like "lat: 40.123, lon: -74.456" or "40.123, -74.456"
    coord_pattern = r'(-?\d+\.?\d*)\s*[,:]\s*(-?\d+\.?\d*)'
    matches = re.findall(coord_pattern, text)
    
    if matches:
        try:
            lat = float(matches[0][0])
            lon = float(matches[0][1])
            # Validate reasonable coordinates
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
        except ValueError:
            pass
    
    return None, None

def scrape_ship_location(ship_name):
    """
    Scrape shipnext.com for ship destination information
    Uses direct vessel URL: https://shipnext.com/vessel/9283887-sagittarius-leader
    """
    try:
        # Direct URL to Sagittarius Leader vessel page
        vessel_url = "https://shipnext.com/vessel/9283887-sagittarius-leader"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        print(f"Fetching vessel page from shipnext.com...")
        response = requests.get(vessel_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract destination information from the vessel detail page
        location_data = extract_from_shipnext_detail(soup, ship_name)
        
        return location_data
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Scraping error: {e}")
        return None

def extract_from_shipnext_search(soup, ship_name):
    """Extract destination/location data from shipnext.com search results"""
    location_data = {
        'location_text': None,
        'latitude': None,
        'longitude': None,
        'speed': None,
        'heading': None
    }
    
    # Look for destination information
    # ShipNext typically shows destination port information
    text_content = soup.get_text()
    
    # Try to find destination port information
    destination_patterns = [
        r'Destination[:\s]+([^,\n]+)',
        r'To[:\s]+([^,\n]+)',
        r'Port[:\s]+([^,\n]+)',
        r'Heading[:\s]+to[:\s]+([^,\n]+)',
        r'ETA[:\s]+([^,\n]+)',
    ]
    
    for pattern in destination_patterns:
        match = re.search(pattern, text_content, re.I)
        if match:
            location_text = match.group(1).strip()
            # Clean up the location text
            location_text = re.sub(r'\s+', ' ', location_text)
            location_text = location_text.split(',')[0].strip()  # Take first part if comma-separated
            location_text = location_text.split('\n')[0].strip()  # Take first line
            location_data['location_text'] = location_text
            break
    
    # Try to find coordinates in text
    lat, lon = extract_coordinates_from_text(text_content)
    if lat and lon:
        location_data['latitude'] = lat
        location_data['longitude'] = lon
    
    # If we have destination text but no coordinates, try geocoding
    if location_data['location_text'] and not location_data['latitude']:
        lat, lon = geocode_location(location_data['location_text'])
        if lat and lon:
            location_data['latitude'] = lat
            location_data['longitude'] = lon
    
    # Extract speed if available
    speed_match = re.search(r'Speed[:\s]+([\d.]+)\s*(?:knots?|kn)?', text_content, re.I)
    if speed_match:
        try:
            location_data['speed'] = float(speed_match.group(1))
        except ValueError:
            pass
    
    # Extract heading if available
    heading_match = re.search(r'Heading[:\s]+([\d.]+)', text_content, re.I)
    if heading_match:
        try:
            location_data['heading'] = float(heading_match.group(1))
        except ValueError:
            pass
    
    return location_data if location_data['latitude'] or location_data['location_text'] else None

def extract_from_shipnext_detail(soup, ship_name):
    """Extract destination/location data from shipnext.com detail page"""
    location_data = {
        'location_text': None,
        'latitude': None,
        'longitude': None,
        'speed': None,
        'heading': None
    }
    
    # Look for map or coordinate data in script tags
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # Look for lat/lng in JavaScript
            lat_match = re.search(r'lat[itude]*["\']?\s*[:=]\s*(-?\d+\.?\d*)', script.string, re.I)
            lng_match = re.search(r'lng|lon[gitude]*["\']?\s*[:=]\s*(-?\d+\.?\d*)', script.string, re.I)
            
            if lat_match and lng_match:
                try:
                    location_data['latitude'] = float(lat_match.group(1))
                    location_data['longitude'] = float(lng_match.group(1))
                    break
                except ValueError:
                    pass
    
    # Extract text content
    text_content = soup.get_text()
    
    # Try to find coordinates in text
    if not location_data['latitude']:
        lat, lon = extract_coordinates_from_text(text_content)
        if lat and lon:
            location_data['latitude'] = lat
            location_data['longitude'] = lon
    
    # Look for destination port information (ShipNext focus)
    destination_patterns = [
        r'Destination[:\s]+([^,\n]+)',
        r'To[:\s]+([^,\n]+)',
        r'Port[:\s]+([^,\n]+)',
        r'Heading[:\s]+to[:\s]+([^,\n]+)',
        r'Next Port[:\s]+([^,\n]+)',
        r'ETA[:\s]+([^,\n]+)',
        r'Current Port[:\s]+([^,\n]+)',
        r'Location[:\s]+([^,\n]+)',
    ]
    
    for pattern in destination_patterns:
        match = re.search(pattern, text_content, re.I)
        if match:
            location_text = match.group(1).strip()
            # Clean up the location text
            location_text = re.sub(r'\s+', ' ', location_text)
            location_text = location_text.split(',')[0].strip()
            location_text = location_text.split('\n')[0].strip()
            # Skip if it looks like a date (ETA)
            if not re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', location_text):
                location_data['location_text'] = location_text
                break
    
    # Geocode destination if needed
    if location_data['location_text'] and not location_data['latitude']:
        lat, lon = geocode_location(location_data['location_text'])
        if lat and lon:
            location_data['latitude'] = lat
            location_data['longitude'] = lon
    
    # Extract speed if available
    speed_match = re.search(r'Speed[:\s]+([\d.]+)\s*(?:knots?|kn)?', text_content, re.I)
    if speed_match:
        try:
            location_data['speed'] = float(speed_match.group(1))
        except ValueError:
            pass
    
    # Extract heading if available
    heading_match = re.search(r'Heading[:\s]+([\d.]+)', text_content, re.I)
    if heading_match:
        try:
            location_data['heading'] = float(heading_match.group(1))
        except ValueError:
            pass
    
    # Return data if we have at least location text or coordinates
    return location_data if (location_data['latitude'] or location_data['location_text']) else None
