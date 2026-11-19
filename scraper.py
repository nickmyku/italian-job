import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
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

def parse_eta_relative(relative_text):
    """
    Parse VesselFinder relative ETA strings like "(in 13 days)" or "(2 days ago)".

    Returns days until ETA (negative if past), or None if unparseable.
    """
    if not relative_text:
        return None

    text = relative_text.strip().lower()
    text = text.strip('()').strip()

    if re.search(r'\barrived\b', text):
        return -1

    in_match = re.search(
        r'\bin\s+(\d+)\s*(day|days|hour|hours|hr|hrs|minute|minutes|min|mins)\b',
        text,
    )
    if in_match:
        amount = int(in_match.group(1))
        unit = in_match.group(2)
        if unit.startswith('day'):
            return amount
        # Same calendar day for hour/minute countdowns
        return 0

    ago_match = re.search(
        r'\b(\d+)\s*(day|days|hour|hours|hr|hrs|minute|minutes|min|mins)\s+ago\b',
        text,
    )
    if ago_match:
        amount = int(ago_match.group(1))
        unit = ago_match.group(2)
        if unit.startswith('day'):
            return -amount
        return -1

    if re.search(r'\btoday\b', text):
        return 0

    return None


def parse_eta_text_to_iso(eta_text, reference_date=None):
    """
    Parse VesselFinder-style ETA text ("Dec 2, 04:00") into an ISO date (YYYY-MM-DD).

    Year is often omitted; infer current year, rolling forward if the date is
    more than one day behind the reference date.
    """
    if not eta_text:
        return None

    if reference_date is None:
        reference_date = datetime.utcnow().date()
    elif hasattr(reference_date, 'date'):
        reference_date = reference_date.date()

    cleaned = re.sub(r'^ETA:\s*', '', eta_text.strip(), flags=re.I)

    # "Dec 2, 04:00" or "Dec 2, 2026, 04:00" or "Dec 2"
    month_day = re.search(
        r'\b([A-Za-z]{3,9})\s+(\d{1,2})(?:,\s*(\d{4}))?(?:,\s*\d{1,2}:\d{2})?\b',
        cleaned,
    )
    if month_day:
        month_name = month_day.group(1)
        day = int(month_day.group(2))
        year = int(month_day.group(3)) if month_day.group(3) else reference_date.year
        try:
            eta_date = datetime.strptime(f'{month_name} {day} {year}', '%b %d %Y').date()
        except ValueError:
            try:
                eta_date = datetime.strptime(f'{month_name} {day} {year}', '%B %d %Y').date()
            except ValueError:
                return None
        if month_day.group(3) is None and eta_date < (reference_date - timedelta(days=1)):
            try:
                eta_date = eta_date.replace(year=year + 1)
            except ValueError:
                return None
        return eta_date.isoformat()

    # ShipNext style: DD-MM-YYYY
    dmy = re.search(r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b', cleaned)
    if dmy:
        day, month, year = int(dmy.group(1)), int(dmy.group(2)), int(dmy.group(3))
        try:
            return datetime(year, month, day).date().isoformat()
        except ValueError:
            return None

    return None


def extract_shipnext_eta_and_transit(text):
    """
    Extract ETA and in-transit flag from ShipNext voyage prose.

    Example: "Estimated time of arrival at Kawasaki, Japan is 16-11-2026 at 20:20."
    """
    result = {
        'eta_text': None,
        'eta': None,
        'in_transit': None,
    }
    if not text:
        return result

    if re.search(r'currently on route to', text, re.I):
        result['in_transit'] = True
    elif re.search(r'\barrived\b|\bin port\b|\bat anchorage\b|\bmoored\b', text, re.I):
        result['in_transit'] = False

    eta_match = re.search(
        r'Estimated time of arrival[^.]{0,120}?is\s+(\d{1,2}-\d{1,2}-\d{4})(?:\s+at\s+(\d{1,2}:\d{2}))?',
        text,
        re.I,
    )
    if eta_match:
        date_part = eta_match.group(1)
        time_part = eta_match.group(2)
        result['eta_text'] = f'{date_part} {time_part}'.strip() if time_part else date_part
        result['eta'] = parse_eta_text_to_iso(date_part)
        print(f"[DEBUG] ShipNext ETA: {result['eta_text']} (iso={result['eta']})")

    return result


def extract_from_vesselfinder(soup):
    """
    Extract current destination and origin (last port) from VesselFinder HTML.

    ShipNext voyage prose often lags one voyage behind AIS. VesselFinder exposes
    the current AIS destination and last port in structured page sections.
    """
    location_data = {
        'location_text': None,
        'origin_city': None,
        'latitude': None,
        'longitude': None,
        'eta_text': None,
        'eta': None,
        'eta_days': None,
        'in_transit': None,
    }

    dest_block = soup.select_one('div.vi__r1.vi__sbt')
    if dest_block:
        dest_link = dest_block.select_one('a._npNa')
        if dest_link:
            dest_text = dest_link.get_text(' ', strip=True)
            if dest_text and len(dest_text) > 2:
                location_data['location_text'] = dest_text
                print(f"[DEBUG] VesselFinder destination: {dest_text}")
        eta_span = dest_block.select_one('span._mcol12ext')
        if eta_span:
            eta_text = eta_span.get_text(' ', strip=True)
            # Normalize "ETA: Dec 2, 04:00" -> "Dec 2, 04:00"
            eta_text = re.sub(r'^ETA:\s*', '', eta_text, flags=re.I).strip()
            if eta_text:
                location_data['eta_text'] = eta_text
                location_data['eta'] = parse_eta_text_to_iso(eta_text)
                print(f"[DEBUG] VesselFinder ETA: {eta_text} (iso={location_data['eta']})")
        relative_span = dest_block.select_one('span._arrTde')
        if relative_span:
            relative_text = relative_span.get_text(' ', strip=True)
            eta_days = parse_eta_relative(relative_text)
            if eta_days is not None:
                location_data['eta_days'] = eta_days
                location_data['in_transit'] = eta_days >= 0
                print(f"[DEBUG] VesselFinder ETA relative: {relative_text} -> {eta_days} days")

    origin_block = soup.select_one('div.vi__r1.vi__stp')
    if origin_block:
        origin_link = origin_block.select_one('a._npNa')
        if origin_link:
            origin_text = origin_link.get_text(' ', strip=True)
            if origin_text and len(origin_text) > 2:
                location_data['origin_city'] = origin_text
                print(f"[DEBUG] VesselFinder origin (last port): {origin_text}")

    # Optional coarse coordinates from embedded JSON (prefer ShipNext DMS when available)
    djson = soup.select_one('#djson[data-json]')
    if djson and djson.get('data-json'):
        try:
            payload = json.loads(djson['data-json'])
            lat = payload.get('ship_lat')
            lon = payload.get('ship_lon')
            if lat is not None and lon is not None:
                lat_f = float(lat)
                lon_f = float(lon)
                if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
                    location_data['latitude'] = lat_f
                    location_data['longitude'] = lon_f
                    print(f"[DEBUG] VesselFinder coordinates: Latitude={lat_f}, Longitude={lon_f}")
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            print(f"[DEBUG] VesselFinder coordinate parse error: {e}")

    return location_data if (
        location_data['location_text'] or location_data['origin_city'] or location_data['latitude']
    ) else None


def scrape_vesselfinder_voyage(imo='9505900'):
    """Fetch current voyage ports from VesselFinder for the given IMO."""
    try:
        url = f"https://www.vesselfinder.com/vessels/details/{imo}"
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }
        print(f"Fetching voyage data from VesselFinder ({url})...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        return extract_from_vesselfinder(soup)
    except requests.exceptions.RequestException as e:
        print(f"VesselFinder request error: {e}")
        return None
    except Exception as e:
        print(f"VesselFinder scraping error: {e}")
        return None


def merge_voyage_ports(location_data, voyage_data):
    """
    Prefer VesselFinder current destination/origin over ShipNext voyage prose.

    ShipNext often still describes the previous completed voyage after departure.
    VesselFinder ETA/relative countdown is preferred when present; ShipNext ETA
    is kept only as a fallback.
    """
    if not location_data:
        return voyage_data
    if not voyage_data:
        return location_data

    if voyage_data.get('location_text'):
        prev = location_data.get('location_text')
        location_data['location_text'] = voyage_data['location_text']
        if prev and prev != voyage_data['location_text']:
            print(
                f"[DEBUG] Overriding ShipNext destination '{prev}' "
                f"with VesselFinder '{voyage_data['location_text']}'"
            )
    if voyage_data.get('origin_city'):
        prev = location_data.get('origin_city')
        location_data['origin_city'] = voyage_data['origin_city']
        if prev and prev != voyage_data['origin_city']:
            print(
                f"[DEBUG] Overriding ShipNext origin '{prev}' "
                f"with VesselFinder '{voyage_data['origin_city']}'"
            )

    # Prefer VesselFinder ETA fields; keep ShipNext values when VF has none
    if voyage_data.get('eta_text'):
        location_data['eta_text'] = voyage_data['eta_text']
    if voyage_data.get('eta'):
        location_data['eta'] = voyage_data['eta']
    if voyage_data.get('eta_days') is not None:
        location_data['eta_days'] = voyage_data['eta_days']
    if voyage_data.get('in_transit') is not None:
        location_data['in_transit'] = voyage_data['in_transit']

    # Keep ShipNext coordinates when present (more precise DMS); else use VesselFinder
    if not location_data.get('latitude') and voyage_data.get('latitude') is not None:
        location_data['latitude'] = voyage_data['latitude']
        location_data['longitude'] = voyage_data['longitude']

    return location_data


def scrape_ship_location(ship_name):
    """
    Scrape ship location information for VENUS SPIRIT.

    Coordinates come primarily from shipnext.com.
    Current origin/destination come from VesselFinder AIS data, because
    ShipNext voyage text often lags one voyage behind.
    """
    try:
        # Direct URL to VENUS SPIRIT vessel page
        vessel_url = "https://shipnext.com/vessel/9505900-venus-spirit"
        
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

        # Override stale ShipNext voyage ports with current AIS ports from VesselFinder
        voyage_data = scrape_vesselfinder_voyage('9505900')
        location_data = merge_voyage_ports(location_data, voyage_data)
        
        # Print final coordinates for debugging
        if location_data and location_data.get('latitude') and location_data.get('longitude'):
            print(f"[DEBUG] Final ship coordinates: Latitude={location_data['latitude']}, Longitude={location_data['longitude']}")
        elif location_data:
            print(f"[DEBUG] Location data found but no coordinates. Location text: {location_data.get('location_text', 'N/A')}")
        else:
            print("[DEBUG] No location data found")

        if location_data:
            print(f"[DEBUG] Final origin city: {location_data.get('origin_city')}")
            print(f"[DEBUG] Final destination text: {location_data.get('location_text')}")
        
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
        'longitude': None
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
    
    return location_data if location_data['latitude'] or location_data['location_text'] else None

def extract_from_shipnext_detail(soup, ship_name, response_text=None):
    """Extract destination/location data from shipnext.com detail page"""
    location_data = {
        'location_text': None,
        'origin_city': None,
        'latitude': None,
        'longitude': None,
        'eta_text': None,
        'eta': None,
        'eta_days': None,
        'in_transit': None,
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

    # Parse ShipNext ETA / transit status from voyage prose (VesselFinder may override).
    # Prefer parsed text: raw HTML inserts comment markers around the ETA date.
    shipnext_eta = extract_shipnext_eta_and_transit(text_content)
    if not shipnext_eta.get('eta') and response_text:
        # Fallback: strip HTML comments then retry on raw markup
        cleaned_html = re.sub(r'<!--.*?-->', '', response_text, flags=re.S)
        shipnext_eta = extract_shipnext_eta_and_transit(
            BeautifulSoup(cleaned_html, 'html.parser').get_text(' ')
        )
    if shipnext_eta.get('eta_text'):
        location_data['eta_text'] = shipnext_eta['eta_text']
    if shipnext_eta.get('eta'):
        location_data['eta'] = shipnext_eta['eta']
        # Derive days-until when VesselFinder relative countdown is unavailable
        try:
            eta_date = datetime.strptime(shipnext_eta['eta'], '%Y-%m-%d').date()
            today = datetime.utcnow().date()
            location_data['eta_days'] = (eta_date - today).days
        except ValueError:
            pass
    if shipnext_eta.get('in_transit') is not None:
        location_data['in_transit'] = shipnext_eta['in_transit']
    
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

    if location_data.get('eta_text') or location_data.get('eta_days') is not None:
        print(
            f"[DEBUG] Final ETA: text={location_data.get('eta_text')}, "
            f"iso={location_data.get('eta')}, days={location_data.get('eta_days')}, "
            f"in_transit={location_data.get('in_transit')}"
        )
    
    return location_data if (location_data['latitude'] or location_data['location_text']) else None
