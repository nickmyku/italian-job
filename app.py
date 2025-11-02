from flask import Flask, jsonify, send_from_directory, url_for
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from scraper import scrape_ship_location
from scheduler import start_scheduler

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
    return send_from_directory('static', 'index.html')

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

if __name__ == '__main__':
    init_db()
    start_scheduler()
    app.run(host='0.0.0.0', port=3000, debug=True)
