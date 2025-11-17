from flask import Flask, jsonify, send_from_directory, url_for, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3
import os
import secrets
from datetime import datetime
from functools import wraps
from scraper import scrape_ship_location
from scheduler import start_scheduler

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

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
    """Initialize the database with ship locations and API keys tables"""
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
    
    # Create API keys table
    c.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_used TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Create a default API key if none exists
    c.execute('SELECT COUNT(*) FROM api_keys WHERE is_active = 1')
    if c.fetchone()[0] == 0:
        default_key = os.environ.get('API_KEY', secrets.token_urlsafe(32))
        c.execute('''
            INSERT INTO api_keys (key, name, created_at, is_active)
            VALUES (?, ?, ?, 1)
        ''', (default_key, 'Default Key', datetime.now().isoformat()))
        print(f"\n{'='*80}")
        print(f"GENERATED DEFAULT API KEY: {default_key}")
        print(f"Store this key securely! You'll need it to make POST requests.")
        print(f"You can also set a custom key using the API_KEY environment variable.")
        print(f"{'='*80}\n")
    
    conn.commit()
    conn.close()

def require_api_key(f):
    """Decorator to require API key authentication for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header or query parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'success': False,
                'message': 'API key is required. Include it in X-API-Key header or api_key query parameter.'
            }), 401
        
        # Validate API key
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, is_active FROM api_keys WHERE key = ?', (api_key,))
        result = c.fetchone()
        
        if not result or result[1] != 1:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Invalid or inactive API key'
            }), 403
        
        # Update last_used timestamp
        c.execute('UPDATE api_keys SET last_used = ? WHERE id = ?', 
                 (datetime.now().isoformat(), result[0]))
        conn.commit()
        conn.close()
        
        return f(*args, **kwargs)
    return decorated_function

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
@limiter.limit("60 per minute")  # Allow at least once per minute updates
@require_api_key
def manual_update():
    """Manually trigger an update (requires API key authentication)"""
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
    init_db()
    
    # Start scheduler - singleton pattern in scheduler.py prevents multiple instances
    # Disable reloader to prevent scheduler from being killed on code changes
    start_scheduler()
    app.run(host='0.0.0.0', port=3000, debug=False, use_reloader=False)
