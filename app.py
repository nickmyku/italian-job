from flask import Flask, jsonify, send_from_directory, url_for
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from scraper import scrape_ship_location
from scheduler import start_scheduler
from screenshot import SCREENSHOTS_DIR, ensure_screenshots_dir

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

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

@app.route('/')
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
    if filename.endswith('.js') or filename.endswith('.css'):
        response.headers['Cache-Control'] = 'public, max-age=3600'
    return response

@app.route('/api/location')
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

@app.route('/api/screenshots')
def list_screenshots():
    """List all available screenshots"""
    ensure_screenshots_dir()
    
    screenshots = []
    if os.path.exists(SCREENSHOTS_DIR):
        for filename in sorted(os.listdir(SCREENSHOTS_DIR), reverse=True):
            if filename.endswith('.bmp'):
                filepath = os.path.join(SCREENSHOTS_DIR, filename)
                stat = os.stat(filepath)
                screenshots.append({
                    'filename': filename,
                    'url': f'/api/screenshots/{filename}',
                    'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'size': stat.st_size
                })
    
    return jsonify({'screenshots': screenshots})

@app.route('/api/screenshots/<filename>')
def get_screenshot(filename):
    """Serve a specific screenshot"""
    ensure_screenshots_dir()
    
    # Security: ensure filename doesn't contain path traversal
    if '../' in filename or filename not in os.listdir(SCREENSHOTS_DIR):
        return jsonify({'error': 'Screenshot not found'}), 404
    
    return send_from_directory(SCREENSHOTS_DIR, filename)

@app.route('/api/screenshots/latest')
def get_latest_screenshot():
    """Get the latest screenshot"""
    ensure_screenshots_dir()
    
    if not os.path.exists(SCREENSHOTS_DIR):
        return jsonify({'error': 'No screenshots available'}), 404
    
    screenshots = [f for f in os.listdir(SCREENSHOTS_DIR) if f.endswith('.bmp')]
    if not screenshots:
        return jsonify({'error': 'No screenshots available'}), 404
    
    # Sort by filename (which includes timestamp) to get latest
    latest = sorted(screenshots, reverse=True)[0]
    
    return send_from_directory(SCREENSHOTS_DIR, latest)

@app.route('/screenshots/latest/location.bmp')
def get_latest_screenshot_bmp():
    """Serve the latest screenshot at /screenshots/latest/location.bmp"""
    ensure_screenshots_dir()
    
    latest_filepath = os.path.join(SCREENSHOTS_DIR, 'latest', 'location.bmp')
    
    if not os.path.exists(latest_filepath):
        return jsonify({'error': 'Latest screenshot not available'}), 404
    
    return send_from_directory(os.path.join(SCREENSHOTS_DIR, 'latest'), 'location.bmp')

if __name__ == '__main__':
    init_db()
    
    # Ensure screenshots directory exists
    ensure_screenshots_dir()
    
    # Start scheduler - singleton pattern in scheduler.py prevents multiple instances
    # Disable reloader to prevent scheduler from being killed on code changes
    start_scheduler()
    app.run(host='0.0.0.0', port=3000, debug=True, use_reloader=False)
