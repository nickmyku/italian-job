from flask import Flask, jsonify, send_from_directory, url_for, request, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3
import os
from datetime import datetime
from scraper import scrape_ship_location
from scheduler import start_scheduler
import re

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Comprehensive list of bot user agents
BOT_USER_AGENTS = [
    r'bot', r'crawl', r'spider', r'scrape', r'slurp', r'baidu', r'yandex',
    r'duckduck', r'facebook', r'archive', r'semrush', r'ahrefs', r'mj12',
    r'dotbot', r'petalbot', r'bingpreview', r'google', r'bing', r'yahoo',
    r'curl', r'wget', r'python-requests', r'scrapy', r'httpx', r'axios',
    r'go-http-client', r'java/', r'apache-httpclient', r'okhttp',
    r'pycurl', r'libwww-perl', r'php/', r'ruby', r'nutch', r'ia_archiver',
    r'masscan', r'nmap', r'zgrab', r'shodan', r'censys', r'zmap'
]

# Compile bot patterns for performance
BOT_PATTERN = re.compile('|'.join(BOT_USER_AGENTS), re.IGNORECASE)

def is_bot(user_agent):
    """Check if the user agent is a bot"""
    if not user_agent:
        return True  # Block requests without user agent
    return bool(BOT_PATTERN.search(user_agent))

@app.before_request
def block_bots():
    """Middleware to block bots and crawlers"""
    # Allow robots.txt
    if request.path == '/robots.txt':
        return None
    
    user_agent = request.headers.get('User-Agent', '')
    
    # Block if no user agent or if it matches bot patterns
    if is_bot(user_agent):
        abort(403)  # Forbidden
    
    # Block suspicious patterns
    # Check for common bot behaviors
    if not user_agent or len(user_agent) < 10:
        abort(403)
    
    # Block if Accept header is missing (most browsers send this)
    if not request.headers.get('Accept'):
        abort(403)
    
    return None

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

@app.route('/robots.txt')
def robots():
    """Serve robots.txt file"""
    return send_from_directory('static', 'robots.txt')

@app.route('/')
@limiter.limit("30 per minute")
def index():
    """Serve the main HTML page"""
    response = send_from_directory('static', 'index.html')
    # Add cache control headers to prevent caching issues
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Explicit routes for static files to ensure they're served correctly
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    response = send_from_directory('static', filename)
    # Add cache headers for static files
    if filename.endswith('.js') or filename.endswith('.css') or filename.endswith('.ico'):
        response.headers['Cache-Control'] = 'public, max-age=3600'
    return response

# Route to serve screenshots directly at /screenshots/
@app.route('/screenshots/<path:filename>')
def screenshots(filename):
    """Serve screenshot files"""
    response = send_from_directory('static/screenshots', filename)
    # No caching for screenshots - always serve the latest
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/location')
@limiter.limit("20 per minute")
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
@limiter.limit("20 per minute")
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
@limiter.limit("5 per minute")
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
    init_db()
    
    # Start scheduler - singleton pattern in scheduler.py prevents multiple instances
    # Disable reloader to prevent scheduler from being killed on code changes
    start_scheduler()
    app.run(host='0.0.0.0', port=3000, debug=True, use_reloader=False)
