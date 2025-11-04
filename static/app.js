// Initialize map
let map;
let marker;
let shipMarker;

// Default coordinates (will be updated when data loads)
const defaultCoords = [0, 0];

// Initialize map
function initMap() {
    map = L.map('map').setView(defaultCoords, 2);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '? OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
}

// Update map with ship location
function updateMap(locationData) {
    if (!locationData) {
        showStatus('No destination data available', 'error');
        return;
    }
    
    // Update info panel first (even if no coordinates)
    updateInfoPanel(locationData);
    
    // Only update map if we have coordinates
    if (!locationData.latitude || !locationData.longitude) {
        if (locationData.location_text) {
            showStatus('Destination found but no coordinates available', 'success');
        } else {
            showStatus('No destination data available', 'error');
        }
        return;
    }
    
    const lat = locationData.latitude;
    const lon = locationData.longitude;
    
    // Remove existing marker
    if (shipMarker) {
        map.removeLayer(shipMarker);
    }
    
    // Create custom cargo ship icon using SVG
    const cargoShipIconSvg = `
        <svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
            <!-- Background circle -->
            <circle cx="30" cy="30" r="26" fill="#ffffff" stroke="#667eea" stroke-width="2.5" opacity="0.95"/>
            <g transform="translate(30, 30)">
                <!-- Ship hull -->
                <path d="M -20 8 L -18 5 L 18 5 L 20 8 L 20 12 L -20 12 Z" fill="#2c3e50"/>
                <!-- Ship deck -->
                <rect x="-18" y="5" width="36" height="3" fill="#34495e"/>
                <!-- Cargo containers -->
                <rect x="-15" y="-2" width="6" height="7" fill="#e74c3c"/>
                <rect x="-8" y="-2" width="6" height="7" fill="#3498db"/>
                <rect x="-1" y="-2" width="6" height="7" fill="#f39c12"/>
                <rect x="6" y="-2" width="6" height="7" fill="#27ae60"/>
                <rect x="13" y="-2" width="4" height="7" fill="#9b59b6"/>
                <!-- Second row of containers -->
                <rect x="-12" y="-9" width="5" height="7" fill="#e67e22"/>
                <rect x="-6" y="-9" width="5" height="7" fill="#1abc9c"/>
                <rect x="0" y="-9" width="5" height="7" fill="#e74c3c"/>
                <rect x="6" y="-9" width="5" height="7" fill="#3498db"/>
                <!-- Ship bridge/superstructure -->
                <rect x="8" y="-15" width="8" height="20" fill="#34495e"/>
                <rect x="9" y="-14" width="6" height="6" fill="#ecf0f1" opacity="0.8"/>
                <!-- Container lines -->
                <line x1="-15" y1="-2" x2="-15" y2="5" stroke="#000" stroke-width="0.3" opacity="0.3"/>
                <line x1="-9" y1="-2" x2="-9" y2="5" stroke="#000" stroke-width="0.3" opacity="0.3"/>
                <line x1="-3" y1="-2" x2="-3" y2="5" stroke="#000" stroke-width="0.3" opacity="0.3"/>
                <line x1="3" y1="-2" x2="3" y2="5" stroke="#000" stroke-width="0.3" opacity="0.3"/>
                <line x1="9" y1="-2" x2="9" y2="5" stroke="#000" stroke-width="0.3" opacity="0.3"/>
                <line x1="15" y1="-2" x2="15" y2="5" stroke="#000" stroke-width="0.3" opacity="0.3"/>
            </g>
        </svg>
    `;
    
    const shipIcon = L.divIcon({
        className: 'ship-marker',
        html: cargoShipIconSvg,
        iconSize: [60, 60],
        iconAnchor: [30, 30],
        popupAnchor: [0, -30]
    });
    
    // Add marker
    shipMarker = L.marker([lat, lon], { icon: shipIcon }).addTo(map);
    
    // Create popup content
    let popupContent = `<strong>Sagittarius Leader</strong><br>`;
    if (locationData.location_text) {
        popupContent += `Destination: ${locationData.location_text}<br>`;
    }
    popupContent += `Coordinates: ${lat.toFixed(6)}, ${lon.toFixed(6)}<br>`;
    if (locationData.speed) {
        popupContent += `Speed: ${locationData.speed} knots<br>`;
    }
    if (locationData.heading) {
        popupContent += `Heading: ${locationData.heading}°`;
    }
    
    shipMarker.bindPopup(popupContent);
    
    // Center map on ship
    map.setView([lat, lon], 6);
    
    // Update info panel
    updateInfoPanel(locationData);
}

// Update info panel
function updateInfoPanel(data) {
    if (data.timestamp) {
        const date = new Date(data.timestamp);
        document.getElementById('lastUpdated').textContent = date.toLocaleString();
    }
    
    document.getElementById('locationText').textContent = 
        data.location_text || 'Unknown';
    document.getElementById('speed').textContent = 
        data.speed ? `${data.speed} knots` : '-';
    document.getElementById('heading').textContent = 
        data.heading ? `${data.heading}°` : '-';
    
    if (data.latitude && data.longitude) {
        document.getElementById('coordinates').textContent = 
            `${data.latitude.toFixed(6)}, ${data.longitude.toFixed(6)}`;
    }
}

// Fetch location from API
async function fetchLocation() {
    try {
        showStatus('Loading...', 'loading');
        const response = await fetch('/api/location');
        const data = await response.json();
        
        if (data.success) {
            updateMap(data);
            showStatus('Destination updated successfully', 'success');
        } else {
            showStatus('No destination data found', 'error');
        }
    } catch (error) {
        console.error('Error fetching location:', error);
        showStatus('Error loading location', 'error');
    }
}

// Manual update
async function manualUpdate() {
    try {
        showStatus('Updating destination...', 'loading');
        const response = await fetch('/api/update', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            updateMap(data.data);
            showStatus('Destination updated successfully', 'success');
            // Refresh history
            fetchHistory();
        } else {
            showStatus('Failed to update destination: ' + (data.message || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error updating location:', error);
        showStatus('Error updating destination', 'error');
    }
}

// Fetch history
async function fetchHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '';
        
        if (data.history && data.history.length > 0) {
            data.history.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                
                const date = new Date(item.timestamp);
                const timeStr = date.toLocaleString();
                
                historyItem.innerHTML = `
                    <span class="time">${timeStr}</span>
                    <span class="coords">${item.latitude?.toFixed(4)}, ${item.longitude?.toFixed(4)}</span>
                `;
                
                historyItem.addEventListener('click', () => {
                    map.setView([item.latitude, item.longitude], 8);
                    if (shipMarker) {
                        shipMarker.setLatLng([item.latitude, item.longitude]);
                    }
                });
                
                historyList.appendChild(historyItem);
            });
        } else {
            historyList.innerHTML = '<p style="text-align: center; color: #6c757d;">No history available</p>';
        }
    } catch (error) {
        console.error('Error fetching history:', error);
    }
}

// Show status message
function showStatus(message, type) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;
    
    if (type !== 'loading') {
        setTimeout(() => {
            statusEl.textContent = '';
            statusEl.className = 'status';
        }, 5000);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    fetchLocation();
    fetchHistory();
    
    // Set up event listeners
    document.getElementById('updateBtn').addEventListener('click', manualUpdate);
    document.getElementById('refreshBtn').addEventListener('click', fetchLocation);
    
    // Auto-refresh every 5 minutes
    setInterval(fetchLocation, 5 * 60 * 1000);
});
