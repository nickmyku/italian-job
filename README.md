# Ship Tracker - Sagittarius Leader

A web application that scrapes shipnext.com for the destination information of the ship "Sagittarius Leader" and displays it on an interactive map with daily automatic updates.

## Features

- ?? Web scraping of ship destination information from shipnext.com
- ??? Interactive map visualization using Leaflet.js
- ?? Real-time location display with coordinates, speed, and heading
- ?? Location history tracking
- ?? Automatic daily updates (scheduled for 00:00 UTC)
- ?? Manual update button for on-demand location checks

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the Flask server:
```bash
python app.py
```

The application will be available at `http://localhost:3000`

## How It Works

1. **Backend (Flask)**: 
   - Scrapes shipnext.com for ship destination information
   - Stores location data in SQLite database
   - Provides REST API endpoints for location data
   - Runs scheduled daily updates at midnight UTC

2. **Frontend**:
   - Displays ship location on an interactive map
   - Shows current location, speed, heading, and coordinates
   - Displays recent location history
   - Auto-refreshes every 5 minutes

3. **Scheduler**:
   - Uses APScheduler to automatically update ship location daily
   - Runs initial update when server starts

## API Endpoints

- `GET /api/location` - Get the latest ship location
- `GET /api/history` - Get location history (last 30 entries)
- `POST /api/update` - Manually trigger a location update

## Notes

- The scraper fetches data directly from the Sagittarius Leader vessel page: `https://shipnext.com/vessel/9283887-sagittarius-leader`
- The scraper handles various HTML structures and fallback methods to extract destination information from shipnext.com
- If direct coordinates aren't found, the app attempts geocoding of location text
- The database stores location history for tracking ship movements over time
- Map uses OpenStreetMap tiles for visualization

## Configuration

- Daily update time can be modified in `scheduler.py` (currently set to 00:00 UTC)
- Auto-refresh interval can be changed in `static/app.js` (currently 5 minutes)
