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

def parse_dms_to_decimal(dms_str):
    """
    Parse degrees, minutes, seconds format to decimal degrees
    Supports formats like:
    - 40?42'46"N
    - 40? 42' 46" N
    - 40 deg 42 min 46 sec N
    - 40?42'46.5"N
    Returns tuple (decimal_degrees, hemisphere) or None if parsing fails
    """
    if not dms_str:
        return None
    
    # Pattern for DMS format: degrees?minutes'seconds"hemisphere
    # Supports various separators and formats
    patterns = [
        # Standard format: 40°42'46"N or 40° 42' 46" N
        r'(\d+)[°\s]+(\d+)[\'\s]+(\d+(?:\.\d+)?)[\"\s]*([NSEW])',
        # Alternative format: 40 deg 42 min 46 sec N
        r'(\d+)\s*(?:deg|degree|°)\s+(\d+)\s*(?:min|minute|\')\s+(\d+(?:\.\d+)?)\s*(?:sec|second|\")?\s*([NSEW])',
        # With decimal seconds: 40°42'46.5"N
        r'(\d+)[°\s]+(\d+)[\'\s]+(\d+\.\d+)[\"\s]*([NSEW])',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, dms_str, re.I)
        if match:
            try:
                degrees = int(match.group(1))
                minutes = int(match.group(2))
                seconds = float(match.group(3))
                hemisphere = match.group(4).upper()
                
                # Convert to decimal degrees
                decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
                
                # Apply hemisphere (negative for S and W)
                if hemisphere in ['S', 'W']:
                    decimal = -decimal
                
                return decimal, hemisphere
            except (ValueError, IndexError):
                continue
    
    return None

def extract_dms_coordinates_from_text(text):
    """
    Extract latitude and longitude in DMS format from text
    Returns tuple (latitude, longitude) or (None, None) if not found
    """
    if not text:
        return None, None
    
    # Look for latitude patterns (N/S)
    lat_patterns = [
        r'Lat[itude]*[:]?\s*(\d+[°\s]+\d+[\'\s]+\d+(?:\.\d+)?[\"]?\s*[NS])',
        r'(\d+[°\s]+\d+[\'\s]+\d+(?:\.\d+)?[\"]?\s*[NS])',
    ]
    
    lat_dms = None
    for pattern in lat_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            lat_dms = match.group(1)
            break
    
    # Look for longitude patterns (E/W)
    lon_patterns = [
        r'Lon[gitude]*[:]?\s*(\d+[°\s]+\d+[\'\s]+\d+(?:\.\d+)?[\"]?\s*[EW])',
        r'(\d+[°\s]+\d+[\'\s]+\d+(?:\.\d+)?[\"]?\s*[EW])',
    ]
    
    lon_dms = None
    for pattern in lon_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            lon_dms = match.group(1)
            break
    
    # If we found both, try to parse them
    if lat_dms and lon_dms:
        lat_result = parse_dms_to_decimal(lat_dms)
        lon_result = parse_dms_to_decimal(lon_dms)
        
        if lat_result and lon_result:
            lat, _ = lat_result
            lon, _ = lon_result
            # Validate reasonable coordinates
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                print(f"[DEBUG] Found coordinates from DMS lat/lon patterns: Latitude={lat}, Longitude={lon}")
                return lat, lon
    
    # Try to find DMS coordinates in pairs with forward slash separator
    # Pattern: 051° 18' 06" N / 003° 14' 14" E
    slash_pattern = r'(\d+)[°\s]+(\d+)[\'\s]+(\d+(?:\.\d+)?)[\"]?\s*([NS])\s*/\s*(\d+)[°\s]+(\d+)[\'\s]+(\d+(?:\.\d+)?)[\"]?\s*([EW])'
    slash_match = re.search(slash_pattern, text, re.I)
    if slash_match:
        try:
            lat_deg = int(slash_match.group(1))
            lat_min = int(slash_match.group(2))
            lat_sec = float(slash_match.group(3))
            lat_hem = slash_match.group(4).upper()
            
            lon_deg = int(slash_match.group(5))
            lon_min = int(slash_match.group(6))
            lon_sec = float(slash_match.group(7))
            lon_hem = slash_match.group(8).upper()
            
            # Convert to decimal degrees
            lat = lat_deg + (lat_min / 60.0) + (lat_sec / 3600.0)
            lon = lon_deg + (lon_min / 60.0) + (lon_sec / 3600.0)
            
            # Apply hemisphere (negative for S and W)
            if lat_hem == 'S':
                lat = -lat
            if lon_hem == 'W':
                lon = -lon
            
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                print(f"[DEBUG] Found coordinates from slash pattern: Latitude={lat}, Longitude={lon}")
                return lat, lon
        except (ValueError, IndexError):
            pass
    
    # Try to find DMS coordinates in pairs (common format: lat, lon)
    # Pattern: 40°42'46"N, 74°00'21"W or similar
    pair_pattern = r'(\d+[°\s]+\d+[\'\s]+\d+(?:\.\d+)?[\"]?\s*[NS])[,\s]+(\d+[°\s]+\d+[\'\s]+\d+(?:\.\d+)?[\"]?\s*[EW])'
    pair_match = re.search(pair_pattern, text, re.I)
    if pair_match:
        lat_dms = pair_match.group(1)
        lon_dms = pair_match.group(2)
        lat_result = parse_dms_to_decimal(lat_dms)
        lon_result = parse_dms_to_decimal(lon_dms)
        
        if lat_result and lon_result:
            lat, _ = lat_result
            lon, _ = lon_result
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                print(f"[DEBUG] Found coordinates from pair pattern: Latitude={lat}, Longitude={lon}")
                return lat, lon
    
    return None, None

def extract_coordinates_from_text(text):
    """
    Try to extract coordinates from text
    Supports both decimal degrees and DMS format
    """
    if not text:
        return None, None
    
    # First try DMS format (degrees, minutes, seconds)
    lat, lon = extract_dms_coordinates_from_text(text)
    if lat and lon:
        print(f"[DEBUG] Extracted DMS coordinates: Latitude={lat}, Longitude={lon}")
        return lat, lon
    
    # Fallback to decimal degrees format
    # Look for patterns like "lat: 40.123, lon: -74.456" or "40.123, -74.456"
    coord_pattern = r'(-?\d+\.?\d*)\s*[,:]\s*(-?\d+\.?\d*)'
    matches = re.findall(coord_pattern, text)
    
    if matches:
        try:
            lat = float(matches[0][0])
            lon = float(matches[0][1])
            # Validate reasonable coordinates
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                print(f"[DEBUG] Extracted decimal coordinates: Latitude={lat}, Longitude={lon}")
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
        
        # Print final coordinates for debugging
        if location_data and location_data.get('latitude') and location_data.get('longitude'):
            print(f"[DEBUG] Final ship coordinates: Latitude={location_data['latitude']}, Longitude={location_data['longitude']}")
        elif location_data:
            print(f"[DEBUG] Location data found but no coordinates. Location text: {location_data.get('location_text', 'N/A')}")
        else:
            print("[DEBUG] No location data found")
        
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
        print(f"[DEBUG] Coordinates extracted from search results: Latitude={lat}, Longitude={lon}")
    
    # If we have destination text but no coordinates, try geocoding
    if location_data['location_text'] and not location_data['latitude']:
        lat, lon = geocode_location(location_data['location_text'])
        if lat and lon:
            location_data['latitude'] = lat
            location_data['longitude'] = lon
            print(f"[DEBUG] Coordinates geocoded from location text: Latitude={lat}, Longitude={lon}")
    
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
                    print(f"[DEBUG] Coordinates found in JavaScript: Latitude={location_data['latitude']}, Longitude={location_data['longitude']}")
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
            print(f"[DEBUG] Coordinates extracted from detail page text: Latitude={lat}, Longitude={lon}")
    
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
            print(f"[DEBUG] Coordinates geocoded from destination text: Latitude={lat}, Longitude={lon}")
    
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
