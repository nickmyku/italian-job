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

def extract_coordinates_after_position_string(text):
    """
    Extract coordinates that appear after "Vessel's current position is"
    Returns tuple (latitude, longitude) or (None, None) if not found
    """
    if not text:
        return None, None
    
    # Look for the pattern "Vessel's current position is" followed by coordinates
    # Try various formats that might follow this string (case-insensitive, handles variations)
    position_patterns = [
        # Pattern: "Vessel's current position is" followed by DMS format with slash
        # e.g., "Vessel's current position is 051° 18' 06" N / 003° 14' 14" E"
        r"Vessel'?s\s+current\s+position\s+is\s+(\d+[°\s]+\d+['\s]+\d+(?:\.\d+)?[\"]?\s*[NS])\s*/\s*(\d+[°\s]+\d+['\s]+\d+(?:\.\d+)?[\"]?\s*[EW])",
        # Pattern: "Vessel's current position is" followed by DMS format with comma
        r"Vessel'?s\s+current\s+position\s+is\s+(\d+[°\s]+\d+['\s]+\d+(?:\.\d+)?[\"]?\s*[NS]),\s*(\d+[°\s]+\d+['\s]+\d+(?:\.\d+)?[\"]?\s*[EW])",
        # Pattern: "Vessel's current position is" followed by decimal degrees
        r"Vessel'?s\s+current\s+position\s+is\s*[:\-]?\s*(-?\d+\.?\d*)\s*[,/\s]+\s*(-?\d+\.?\d*)",
    ]
    
    for pattern in position_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            # Try to extract as DMS first
            if len(match.groups()) == 2:
                lat_str = match.group(1)
                lon_str = match.group(2)
                
                # Check if it looks like DMS format
                if '°' in lat_str or '°' in lon_str or "'" in lat_str or "'" in lon_str:
                    lat_result = parse_dms_to_decimal(lat_str)
                    lon_result = parse_dms_to_decimal(lon_str)
                    
                    if lat_result and lon_result:
                        lat, _ = lat_result
                        lon, _ = lon_result
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            print(f"[DEBUG] Found coordinates after 'Vessel's current position is' (DMS): Latitude={lat}, Longitude={lon}")
                            return lat, lon
                else:
                    # Try as decimal degrees
                    try:
                        lat = float(lat_str)
                        lon = float(lon_str)
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            print(f"[DEBUG] Found coordinates after 'Vessel's current position is' (decimal): Latitude={lat}, Longitude={lon}")
                            return lat, lon
                    except ValueError:
                        continue
    
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Fetching vessel page from shipnext.com...")
        response = requests.get(vessel_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Ensure proper encoding
        response.encoding = response.apparent_encoding or 'utf-8'
        
        # Store response text BEFORE parsing (BeautifulSoup might affect response object)
        response_text = response.text
        
        # Debug: Check if position string is in response text
        print(f"[DEBUG] Response text length: {len(response_text)}")
        print(f"[DEBUG] 'Vessel' in response_text: {'Vessel' in response_text}")
        print(f"[DEBUG] 'current position' in response_text: {'current position' in response_text.lower()}")
        
        # Use html.parser (more reliable for text extraction)
        soup = BeautifulSoup(response_text, 'html.parser')
        
        # Debug: Check if position string is in parsed text
        parsed_text = soup.get_text()
        print(f"[DEBUG] Parsed text length: {len(parsed_text)}")
        print(f"[DEBUG] 'Vessel' in parsed_text: {'Vessel' in parsed_text}")
        print(f"[DEBUG] 'current position' in parsed_text: {'current position' in parsed_text.lower()}")
        
        # Extract destination information from the vessel detail page
        location_data = extract_from_shipnext_detail(soup, ship_name, response_text=response_text)
        
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
        'origin_city': None,
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
        r'on route to\s+([^\n\r.]+?)(?:\.|Estimated)',  # "on route to City, Country."
        r'route to\s+([^\n\r.]+?)(?:\.|Estimated)',  # "route to City, Country."
        r'to\s+([A-Z][a-zA-Z\s,]+?)(?:\.|Estimated)',  # "to City, Country."
        r'Destination[:\s]+([^\n]+)',
        r'Port[:\s]+([^\n]+)',
        r'Heading[:\s]+to[:\s]+([^\n]+)',
        r'ETA[:\s]+([^\n]+)',
    ]
    
    for pattern in destination_patterns:
        match = re.search(pattern, text_content, re.I)
        if match:
            location_text = match.group(1).strip()
            # Clean up the location text
            location_text = re.sub(r'\s+', ' ', location_text)
            # Keep both city and country (typically separated by comma)
            # Split by comma and keep first two parts (city, country)
            parts = [p.strip() for p in location_text.split(',')[:2]]
            location_text = ', '.join(parts) if len(parts) > 1 else parts[0] if parts else location_text
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

def extract_from_shipnext_detail(soup, ship_name, response_text=None):
    """Extract destination/location data from shipnext.com detail page"""
    location_data = {
        'location_text': None,
        'origin_city': None,
        'latitude': None,
        'longitude': None,
        'speed': None,
        'heading': None
    }
    
    # Normalize ship name for comparison (case-insensitive, strip whitespace)
    ship_name_normalized = ship_name.strip().lower() if ship_name else ''
    
    # FIRST: Try to extract destination from HTML elements before coordinates
    # Look for destination in common HTML structures
    destination_elements = soup.find_all(['div', 'span', 'td', 'dd', 'p'], 
                                        class_=re.compile(r'destination|port|location|to|next', re.I))
    
    # Also check for data attributes
    destination_data_attrs = soup.find_all(attrs={'data-destination': True}) + \
                            soup.find_all(attrs={'data-port': True}) + \
                            soup.find_all(attrs={'data-location': True})
    
    # Check text content of elements with destination-related keywords
    for elem in destination_elements + destination_data_attrs:
        text = elem.get_text(strip=True)
        if text and len(text) < 100:  # Reasonable destination name length
            # Skip if it looks like coordinates, a date, button/navigation text, or generic labels
            text_lower = text.lower()
            skip_patterns = [
                r'^(show|click|view|see|more|less|add|edit|delete|submit|cancel|close|open|menu|nav|link)',
                r'(button|link|menu|nav|tab|icon|arrow|chevron)',
                r'(trading desk|position|add position|manage)',
                r'^(vessel|ship|boat).*status$',
                r'status$',
                r'latest.*AIS.*Satellite.*data',
                r'AIS.*Satellite.*data',
                r'Satellite.*AIS.*data',
                r'latest.*data',
                r'real.*time.*data',
                r'tracking.*data',
            ]
            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, text_lower, re.I):
                    should_skip = True
                    print(f"[DEBUG] Skipping HTML element text (generic): {text}")
                    break
            
            if not should_skip and \
               not re.match(r'^-?\d+\.?\d*[,\s]+-?\d+\.?\d*$', text) and \
               not re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text) and \
               len(text) > 2 and len(text) < 80:  # Reasonable port name length
                # Skip if it matches the ship name
                if ship_name_normalized and text.strip().lower() == ship_name_normalized:
                    print(f"[DEBUG] Skipping HTML element text (ship name): {text}")
                    should_skip = True
                
                # Only accept if it looks like a place name (contains letters, possibly numbers)
                # Also check that it doesn't end with common non-place suffixes
                if not should_skip and \
                   re.search(r'[a-zA-Z]{3,}', text) and \
                   not re.search(r'(data|status|info|details|more|click|here)$', text_lower):
                    location_data['location_text'] = text
                    print(f"[DEBUG] Destination found in HTML element: {location_data['location_text']}")
                    break
    
    # Also check table structures - common on ship tracking sites
    # Look for table rows with "Destination" or "Port" labels
    if not location_data['location_text']:
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # Check if first cell contains destination-related keywords
                    label_text = cells[0].get_text(strip=True).lower()
                    if any(keyword in label_text for keyword in ['destination', 'port', 'next port', 'to', 'location']):
                        value_text = cells[1].get_text(strip=True)
                        # Clean and validate
                        if value_text and len(value_text) < 100 and len(value_text) > 2:
                            if not re.match(r'^-?\d+\.?\d*[,\s]+-?\d+\.?\d*$', value_text) and \
                               not re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', value_text):
                                location_data['location_text'] = value_text
                                print(f"[DEBUG] Destination found in table: {location_data['location_text']}")
                                break
            if location_data['location_text']:
                break
    
    # Look for destination in JSON data within script tags
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # Look for destination in JSON structures
            destination_json_patterns = [
                r'["\']destination["\']\s*:\s*["\']([^"\']+)["\']',
                r'["\']port["\']\s*:\s*["\']([^"\']+)["\']',
                r'["\']nextPort["\']\s*:\s*["\']([^"\']+)["\']',
                r'["\']destinationPort["\']\s*:\s*["\']([^"\']+)["\']',
                r'destination["\']?\s*:\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in destination_json_patterns:
                dest_match = re.search(pattern, script.string, re.I)
                if dest_match:
                    dest_text = dest_match.group(1).strip()
                    if dest_text and len(dest_text) < 100 and len(dest_text) > 2:
                        location_data['location_text'] = dest_text
                        print(f"[DEBUG] Destination found in JSON/JavaScript: {location_data['location_text']}")
                        break
            
            # Look for lat/lng in JavaScript
            lat_match = re.search(r'lat[itude]*["\']?\s*[:=]\s*(-?\d+\.?\d*)', script.string, re.I)
            lng_match = re.search(r'lng|lon[gitude]*["\']?\s*[:=]\s*(-?\d+\.?\d*)', script.string, re.I)
            
            if lat_match and lng_match:
                try:
                    location_data['latitude'] = float(lat_match.group(1))
                    location_data['longitude'] = float(lng_match.group(1))
                    print(f"[DEBUG] Coordinates found in JavaScript: Latitude={location_data['latitude']}, Longitude={location_data['longitude']}")
                    # Don't break here - continue looking for destination
                except ValueError:
                    pass
    
    # Extract text content
    text_content = soup.get_text()
    
    # FIRST PRIORITY: Look for coordinates after "Vessel's current position is"
    # Try with parsed text first
    print(f"[DEBUG] Checking for position string in text (text length: {len(text_content)})...")
    lat, lon = extract_coordinates_after_position_string(text_content)
    
    # If not found in parsed text, try raw HTML (position string might be in script or special tags)
    if (not lat or not lon) and response_text:
        print(f"[DEBUG] Trying raw HTML text (length: {len(response_text)})...")
        lat, lon = extract_coordinates_after_position_string(response_text)
    
    print(f"[DEBUG] Position string extraction returned: lat={lat}, lon={lon}")
    if lat and lon:
        location_data['latitude'] = lat
        location_data['longitude'] = lon
        print(f"[DEBUG] Coordinates extracted from 'Vessel's current position is': Latitude={lat}, Longitude={lon}")
    else:
        print(f"[DEBUG] Position string extraction failed, checking if 'Vessel' in text: {'Vessel' in text_content}")
        print(f"[DEBUG] Checking if 'current position' in text: {'current position' in text_content.lower()}")
        if response_text:
            print(f"[DEBUG] Checking if 'Vessel' in raw HTML: {'Vessel' in response_text}")
            print(f"[DEBUG] Checking if 'current position' in raw HTML: {'current position' in response_text.lower()}")
    
    # Try to find coordinates in text (only if not found above)
    if not location_data['latitude']:
        lat, lon = extract_coordinates_from_text(text_content)
        if lat and lon:
            location_data['latitude'] = lat
            location_data['longitude'] = lon
            print(f"[DEBUG] Coordinates extracted from detail page text: Latitude={lat}, Longitude={lon}")
    
    # Look for destination port information (ShipNext focus)
    # Try text patterns FIRST (more reliable than HTML element matching)
    # This will override HTML element matching if it finds a better match
    if True:  # Always check text patterns to find the best destination
        destination_patterns = [
            r'on route to\s+([^\n\r.]+?)(?:\.|Estimated)',  # "on route to Iquique, Chile."
            r'route to\s+([^\n\r.]+?)(?:\.|Estimated)',  # "route to Iquique, Chile."
            r'to\s+([A-Z][a-zA-Z\s,]+?)(?:\.|Estimated)',  # "to Iquique, Chile."
            r'from\s+[^\.]+?\s+to\s+([^\n\r.]+?)(?:\.|$)',  # "from X to Iquique, Chile."
            r'Destination[:\s]+([^\n\r]+)',
            r'Port[:\s]+([^\n\r]+)',
            r'Heading[:\s]+to[:\s]+([^\n\r]+)',
            r'Next Port[:\s]+([^\n\r]+)',
            r'Next Port of Call[:\s]+([^\n\r]+)',
            r'Destination Port[:\s]+([^\n\r]+)',
            r'Going to[:\s]+([^\n\r]+)',
            r'Bound for[:\s]+([^\n\r]+)',
            r'Current Port[:\s]+([^\n\r]+)',
            r'Location[:\s]+([^\n\r]+)',
            r'At[:\s]+([^\n\r]+)',  # "At: Port Name"
        ]
        
        for pattern in destination_patterns:
            match = re.search(pattern, text_content, re.I)
            if match:
                location_text = match.group(1).strip()
                # Clean up the location text
                location_text = re.sub(r'\s+', ' ', location_text)
                # Remove common prefixes/suffixes
                location_text = re.sub(r'^(port|to|at|in|for)\s+', '', location_text, flags=re.I)
                # Keep both city and country (typically separated by comma)
                # Split by comma and keep first two parts (city, country)
                parts = [p.strip() for p in location_text.split(',')[:2]]
                location_text = ', '.join(parts) if len(parts) > 1 else parts[0] if parts else location_text
                location_text = location_text.split('\n')[0].strip()
                location_text = location_text.split('/')[0].strip()  # Sometimes "Port A / Port B"
                
                # Skip generic metadata/advertising phrases
                skip_phrases = [
                    r'latest.*AIS.*Satellite.*data',
                    r'AIS.*Satellite.*data',
                    r'Satellite.*AIS.*data',
                    r'latest.*data',
                    r'real.*time.*data',
                    r'tracking.*data',
                    r'vessel.*status',
                    r'ship.*status',
                    r'position.*data',
                    r'location.*data',
                    r'click.*here',
                    r'show.*more',
                    r'view.*details',
                    r'see.*more',
                ]
                should_skip = False
                location_text_lower = location_text.lower()
                for phrase in skip_phrases:
                    if re.search(phrase, location_text_lower, re.I):
                        should_skip = True
                        print(f"[DEBUG] Skipping generic phrase: {location_text}")
                        break
                
                # Skip if it looks like a date, coordinates, too short, or generic phrase
                if not should_skip and \
                   not re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', location_text) and \
                   not re.match(r'^-?\d+\.?\d*[,\s]+-?\d+\.?\d*$', location_text) and \
                   len(location_text) > 2 and len(location_text) < 100 and \
                   re.search(r'[a-zA-Z]{3,}', location_text):  # Must have letters (place name)
                    location_data['location_text'] = location_text
                    print(f"[DEBUG] Destination extracted from text pattern: {location_data['location_text']}")
                    break
        
        # Also try raw HTML if destination not found in parsed text
        if not location_data['location_text'] and response_text:
            for pattern in destination_patterns:
                match = re.search(pattern, response_text, re.I)
                if match:
                    location_text = match.group(1).strip()
                    location_text = re.sub(r'\s+', ' ', location_text)
                    location_text = re.sub(r'^(port|to|at|in|for)\s+', '', location_text, flags=re.I)
                    # Keep both city and country (typically separated by comma)
                    # Split by comma and keep first two parts (city, country)
                    parts = [p.strip() for p in location_text.split(',')[:2]]
                    location_text = ', '.join(parts) if len(parts) > 1 else parts[0] if parts else location_text
                    location_text = location_text.split('\n')[0].strip()
                    location_text = location_text.split('/')[0].strip()
                    
                    # Skip generic metadata/advertising phrases
                    skip_phrases = [
                        r'latest.*AIS.*Satellite.*data',
                        r'AIS.*Satellite.*data',
                        r'Satellite.*AIS.*data',
                        r'latest.*data',
                        r'real.*time.*data',
                        r'tracking.*data',
                        r'vessel.*status',
                        r'ship.*status',
                        r'position.*data',
                        r'location.*data',
                        r'click.*here',
                        r'show.*more',
                        r'view.*details',
                        r'see.*more',
                    ]
                    should_skip = False
                    location_text_lower = location_text.lower()
                    for phrase in skip_phrases:
                        if re.search(phrase, location_text_lower, re.I):
                            should_skip = True
                            print(f"[DEBUG] Skipping generic phrase: {location_text}")
                            break
                    
                    # Skip if it looks like a date, coordinates, too short, or generic phrase
                    if not should_skip and \
                       not re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', location_text) and \
                       not re.match(r'^-?\d+\.?\d*[,\s]+-?\d+\.?\d*$', location_text) and \
                       len(location_text) > 2 and len(location_text) < 100 and \
                       re.search(r'[a-zA-Z]{3,}', location_text):  # Must have letters (place name)
                        location_data['location_text'] = location_text
                        print(f"[DEBUG] Destination extracted from raw HTML: {location_data['location_text']}")
                        break
    
    # Extract origin city (city the ship is proceeding from)
    # Look for origin patterns in text content
    origin_patterns = [
        r'from\s+([^\n\r.]+?)\s+to\s+',  # "from X to Y" - extract X
        r'proceeding\s+from\s+([^\n\r.]+?)(?:\s+to|\s*\.|$)',  # "proceeding from X to Y" or "proceeding from X."
        r'departed\s+from\s+([^\n\r.]+?)(?:\s+to|\s*\.|$)',  # "departed from X"
        r'Origin[:\s]+([^\n\r]+)',  # "Origin: X"
        r'From Port[:\s]+([^\n\r]+)',  # "From Port: X"
        r'Last Port[:\s]+([^\n\r]+)',  # "Last Port: X"
        r'Previous Port[:\s]+([^\n\r]+)',  # "Previous Port: X"
        r'Port of Origin[:\s]+([^\n\r]+)',  # "Port of Origin: X"
    ]
    
    # Try text content first
    for pattern in origin_patterns:
        match = re.search(pattern, text_content, re.I)
        if match:
            origin_text = match.group(1).strip()
            # Clean up the origin text
            origin_text = re.sub(r'\s+', ' ', origin_text)
            # Remove common prefixes/suffixes
            origin_text = re.sub(r'^(port|from|at|in|for)\s+', '', origin_text, flags=re.I)
            # Keep both city and country (typically separated by comma)
            # Split by comma and keep first two parts (city, country)
            parts = [p.strip() for p in origin_text.split(',')[:2]]
            origin_text = ', '.join(parts) if len(parts) > 1 else parts[0] if parts else origin_text
            origin_text = origin_text.split('\n')[0].strip()
            origin_text = origin_text.split('/')[0].strip()  # Sometimes "Port A / Port B"
            
            # Skip generic metadata/advertising phrases
            skip_phrases = [
                r'latest.*AIS.*Satellite.*data',
                r'AIS.*Satellite.*data',
                r'Satellite.*AIS.*data',
                r'latest.*data',
                r'real.*time.*data',
                r'tracking.*data',
                r'vessel.*status',
                r'ship.*status',
                r'position.*data',
                r'location.*data',
                r'click.*here',
                r'show.*more',
                r'view.*details',
                r'see.*more',
            ]
            should_skip = False
            origin_text_lower = origin_text.lower()
            for phrase in skip_phrases:
                if re.search(phrase, origin_text_lower, re.I):
                    should_skip = True
                    print(f"[DEBUG] Skipping generic phrase for origin: {origin_text}")
                    break
            
            # Skip if it looks like a date, coordinates, too short, or generic phrase
            if not should_skip and \
               not re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', origin_text) and \
               not re.match(r'^-?\d+\.?\d*[,\s]+-?\d+\.?\d*$', origin_text) and \
               len(origin_text) > 2 and len(origin_text) < 100 and \
               re.search(r'[a-zA-Z]{3,}', origin_text):  # Must have letters (place name)
                location_data['origin_city'] = origin_text
                print(f"[DEBUG] Origin city extracted from text pattern: {location_data['origin_city']}")
                break
    
    # Also try raw HTML if origin not found in parsed text
    if not location_data['origin_city'] and response_text:
        for pattern in origin_patterns:
            match = re.search(pattern, response_text, re.I)
            if match:
                origin_text = match.group(1).strip()
                origin_text = re.sub(r'\s+', ' ', origin_text)
                origin_text = re.sub(r'^(port|from|at|in|for)\s+', '', origin_text, flags=re.I)
                # Keep both city and country (typically separated by comma)
                # Split by comma and keep first two parts (city, country)
                parts = [p.strip() for p in origin_text.split(',')[:2]]
                origin_text = ', '.join(parts) if len(parts) > 1 else parts[0] if parts else origin_text
                origin_text = origin_text.split('\n')[0].strip()
                origin_text = origin_text.split('/')[0].strip()
                
                # Skip generic metadata/advertising phrases
                skip_phrases = [
                    r'latest.*AIS.*Satellite.*data',
                    r'AIS.*Satellite.*data',
                    r'Satellite.*AIS.*data',
                    r'latest.*data',
                    r'real.*time.*data',
                    r'tracking.*data',
                    r'vessel.*status',
                    r'ship.*status',
                    r'position.*data',
                    r'location.*data',
                    r'click.*here',
                    r'show.*more',
                    r'view.*details',
                    r'see.*more',
                ]
                should_skip = False
                origin_text_lower = origin_text.lower()
                for phrase in skip_phrases:
                    if re.search(phrase, origin_text_lower, re.I):
                        should_skip = True
                        print(f"[DEBUG] Skipping generic phrase for origin: {origin_text}")
                        break
                
                # Skip if it looks like a date, coordinates, too short, or generic phrase
                if not should_skip and \
                   not re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', origin_text) and \
                   not re.match(r'^-?\d+\.?\d*[,\s]+-?\d+\.?\d*$', origin_text) and \
                   len(origin_text) > 2 and len(origin_text) < 100 and \
                   re.search(r'[a-zA-Z]{3,}', origin_text):  # Must have letters (place name)
                    location_data['origin_city'] = origin_text
                    print(f"[DEBUG] Origin city extracted from raw HTML: {location_data['origin_city']}")
                    break
    
    # Also check table structures for origin
    if not location_data['origin_city']:
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # Check if first cell contains origin-related keywords
                    label_text = cells[0].get_text(strip=True).lower()
                    if any(keyword in label_text for keyword in ['origin', 'from', 'last port', 'previous port', 'departed']):
                        value_text = cells[1].get_text(strip=True)
                        # Clean and validate
                        if value_text and len(value_text) < 100 and len(value_text) > 2:
                            if not re.match(r'^-?\d+\.?\d*[,\s]+-?\d+\.?\d*$', value_text) and \
                               not re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', value_text):
                                location_data['origin_city'] = value_text
                                print(f"[DEBUG] Origin city found in table: {location_data['origin_city']}")
                                break
            if location_data['origin_city']:
                break
    
    # Geocode destination if needed
    if location_data['location_text'] and not location_data['latitude']:
        lat, lon = geocode_location(location_data['location_text'])
        if lat and lon:
            location_data['latitude'] = lat
            location_data['longitude'] = lon
            print(f"[DEBUG] Coordinates geocoded from destination text: Latitude={lat}, Longitude={lon}")
    
    # Extract speed if available - try multiple patterns
    speed_patterns = [
        r'Speed[:\s]+([\d.]+)\s*(?:knots?|kn|kts)?',
        r'SOG[:\s]+([\d.]+)\s*(?:knots?|kn|kts)?',  # Speed Over Ground
        r'speed["\']?\s*[:=]\s*([\d.]+)',
        r'"speed"[:\s]*([\d.]+)',
        r'speed[:\s]*([\d.]+)',
    ]
    
    # Try text content first
    for pattern in speed_patterns:
        speed_match = re.search(pattern, text_content, re.I)
        if speed_match:
            try:
                speed_value = float(speed_match.group(1))
                location_data['speed'] = speed_value
                print(f"[DEBUG] Speed extracted: {speed_value}")
                break
            except ValueError:
                continue
    
    # Also check raw HTML if available
    if not location_data['speed'] and response_text:
        for pattern in speed_patterns:
            speed_match = re.search(pattern, response_text, re.I)
            if speed_match:
                try:
                    speed_value = float(speed_match.group(1))
                    location_data['speed'] = speed_value
                    print(f"[DEBUG] Speed extracted from raw HTML: {speed_value}")
                    break
                except ValueError:
                    continue
    
    # Also check JavaScript/JSON data in script tags for speed
    if not location_data['speed']:
        for script in scripts:
            if script.string:
                speed_patterns_js = [
                    r'speed["\']?\s*[:=]\s*([\d.]+)',
                    r'"speed"[:\s]*([\d.]+)',
                    r'speed[:\s]*([\d.]+)',
                ]
                for pattern in speed_patterns_js:
                    speed_match = re.search(pattern, script.string, re.I)
                    if speed_match:
                        try:
                            speed_value = float(speed_match.group(1))
                            location_data['speed'] = speed_value
                            print(f"[DEBUG] Speed extracted from JavaScript: {speed_value}")
                            break
                        except ValueError:
                            continue
                if location_data['speed']:
                    break
    
    # Extract heading if available - try multiple patterns
    heading_patterns = [
        r'Heading[:\s]+([\d.]+)\s*(?:°|deg|degrees)?',
        r'COG[:\s]+([\d.]+)\s*(?:°|deg|degrees)?',  # Course Over Ground
        r'Course[:\s]+([\d.]+)\s*(?:°|deg|degrees)?',
        r'heading["\']?\s*[:=]\s*([\d.]+)',
        r'"heading"[:\s]*([\d.]+)',
        r'heading[:\s]*([\d.]+)',
        r'Bearing[:\s]+([\d.]+)\s*(?:°|deg|degrees)?',
    ]
    
    # Try text content first
    for pattern in heading_patterns:
        heading_match = re.search(pattern, text_content, re.I)
        if heading_match:
            try:
                heading_value = float(heading_match.group(1))
                # Normalize heading to 0-360 range
                heading_value = heading_value % 360
                location_data['heading'] = heading_value
                print(f"[DEBUG] Heading extracted: {heading_value}")
                break
            except ValueError:
                continue
    
    # Also check raw HTML if available
    if not location_data['heading'] and response_text:
        for pattern in heading_patterns:
            heading_match = re.search(pattern, response_text, re.I)
            if heading_match:
                try:
                    heading_value = float(heading_match.group(1))
                    # Normalize heading to 0-360 range
                    heading_value = heading_value % 360
                    location_data['heading'] = heading_value
                    print(f"[DEBUG] Heading extracted from raw HTML: {heading_value}")
                    break
                except ValueError:
                    continue
    
    # Also check JavaScript/JSON data in script tags for heading
    if not location_data['heading']:
        for script in scripts:
            if script.string:
                heading_patterns_js = [
                    r'heading["\']?\s*[:=]\s*([\d.]+)',
                    r'"heading"[:\s]*([\d.]+)',
                    r'heading[:\s]*([\d.]+)',
                    r'course["\']?\s*[:=]\s*([\d.]+)',
                ]
                for pattern in heading_patterns_js:
                    heading_match = re.search(pattern, script.string, re.I)
                    if heading_match:
                        try:
                            heading_value = float(heading_match.group(1))
                            # Normalize heading to 0-360 range
                            heading_value = heading_value % 360
                            location_data['heading'] = heading_value
                            print(f"[DEBUG] Heading extracted from JavaScript: {heading_value}")
                            break
                        except ValueError:
                            continue
                if location_data['heading']:
                    break
    
    # Return data if we have at least location text or coordinates
    # Log what we're returning for debugging
    if location_data['location_text']:
        print(f"[DEBUG] Final destination text: {location_data['location_text']}")
    else:
        print("[DEBUG] WARNING: Destination could not be found by the scraper")
    
    if location_data['origin_city']:
        print(f"[DEBUG] Final origin city: {location_data['origin_city']}")
    else:
        print("[DEBUG] WARNING: Origin city could not be found by the scraper")
    
    if location_data['latitude'] and location_data['longitude']:
        print(f"[DEBUG] Final coordinates: {location_data['latitude']}, {location_data['longitude']}")
    else:
        print("[DEBUG] WARNING: Coordinates could not be found by the scraper")
    
    if location_data['speed'] is not None:
        print(f"[DEBUG] Final speed: {location_data['speed']}")
    else:
        print("[DEBUG] WARNING: Speed could not be found by the scraper")
    
    if location_data['heading'] is not None:
        print(f"[DEBUG] Final heading: {location_data['heading']}")
    else:
        print("[DEBUG] WARNING: Heading could not be found by the scraper")
    
    return location_data if (location_data['latitude'] or location_data['location_text']) else None
