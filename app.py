from flask import Flask, jsonify, send_from_directory, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import sqlite3
import os
from datetime import datetime
from scraper import scrape_ship_location
from scheduler import start_scheduler

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# Configure security headers
Talisman(
    app,
    force_https=False,  # Set to True in production with HTTPS
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,  # 1 year
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com",  # Allow Leaflet from unpkg
        'style-src': "'self' 'unsafe-inline' https://unpkg.com",  # Allow Leaflet CSS from unpkg
        'img-src': "'self' data: https: *.basemaps.cartocdn.com",  # Allow map tiles from CartoDB
        'font-src': "'self' data:",
        'connect-src': "'self'",  # API connections
        'frame-ancestors': "'none'",
    },
    content_security_policy_nonce_in=['script-src', 'style-src'],
    frame_options='DENY',
    content_type_nosniff=True,
    xss_filter=True,
    referrer_policy='strict-origin-when-cross-origin',
    permissions_policy={
        'geolocation': '()',  # Disable geolocation
        'camera': '()',  # Disable camera
        'microphone': '()',  # Disable microphone
    }
)

# Configure Flask-Limiter
# Default: 200 requests per minute for general API usage
# Storage: in-memory (suitable for single-instance deployments)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)

DB_PATH = 'ship_locations.db'

def init_db():
    """Initialize the database with ship locations table"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS ship_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ship_name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            timestamp TEXT NOT NULL,
            location_text TEXT,
            speed REAL,
            heading REAL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database and start scheduler when module is imported
# This ensures proper initialization for both Gunicorn and development server
init_db()
start_scheduler()

@app.route('/')
@limiter.exempt  # No rate limiting on static pages
def index():
    """Serve the main HTML page"""
    response = send_from_directory('static', 'index.html')
    # Add cache control headers to prevent caching issues
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/robots.txt')
@limiter.exempt  # No rate limiting on robots.txt
def robots_txt():
    """Serve the robots.txt file to block bots"""
    response = send_from_directory('.', 'robots.txt')
    response.headers['Content-Type'] = 'text/plain'
    return response

# Explicit routes for static files to ensure they're served correctly
@app.route('/static/<path:filename>')
@limiter.exempt  # No rate limiting on static files
def static_files(filename):
    """Serve static files"""
    response = send_from_directory('static', filename)
    # Add cache headers for static files
    if filename.endswith('.js') or filename.endswith('.css') or filename.endswith('.ico'):
        response.headers['Cache-Control'] = 'public, max-age=3600'
    return response

# Route to serve screenshots directly at /screenshots/
@app.route('/screenshots/<path:filename>')
@limiter.exempt  # No rate limiting on screenshots
def screenshots(filename):
    """Serve screenshot files"""
    response = send_from_directory('static/screenshots', filename)
    # No caching for screenshots - always serve the latest
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/location')
@limiter.limit("120 per minute")  # Higher limit for read operations
def get_location():
    """Get the latest location of Sagittarius Leader"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT latitude, longitude, timestamp, location_text, speed, heading
        FROM ship_locations
        WHERE ship_name = ?
        ORDER BY timestamp DESC
        LIMIT 1
    ''', ('Sagittarius Leader',))
    
    result = c.fetchone()
    conn.close()
    
    if result:
        return jsonify({
            'latitude': result[0],
            'longitude': result[1],
            'timestamp': result[2],
            'location_text': result[3],
            'speed': result[4],
            'heading': result[5],
            'success': True
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No location data found'
        }), 404

@app.route('/api/history')
@limiter.limit("120 per minute")  # Higher limit for read operations
def get_history():
    """Get location history"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT latitude, longitude, timestamp, location_text, speed, heading
        FROM ship_locations
        WHERE ship_name = ?
        ORDER BY timestamp DESC
        LIMIT 30
    ''', ('Sagittarius Leader',))
    
    results = c.fetchall()
    conn.close()
    
    history = []
    for row in results:
        history.append({
            'latitude': row[0],
            'longitude': row[1],
            'timestamp': row[2],
            'location_text': row[3],
            'speed': row[4],
            'heading': row[5]
        })
    
    return jsonify({'history': history})

@app.route('/api/update', methods=['POST'])
@limiter.limit("1 per minute")  # Allow at least once per minute updates
def manual_update():
    """Manually trigger an update"""
    try:
        location_data = scrape_ship_location('Sagittarius Leader')
        if location_data:
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
            return jsonify({'success': True, 'data': location_data})
        else:
            return jsonify({'success': False, 'message': 'Failed to scrape location'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    # Development mode: run Flask's development server
    # Note: init_db() and start_scheduler() are already called at module level
    app.run(host='0.0.0.0', port=3000, debug=False, use_reloader=False)
