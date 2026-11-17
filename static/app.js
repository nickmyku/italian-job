// Initialize map
let map;
let marker;
let shipMarker;
let historyMarkers = [];
let historyLines = [];
let historyData = [];

// Default coordinates (will be updated when data loads)
const defaultCoords = [0, 0];

// Display timestamps in Arizona time (MST year-round; no DST)
const DISPLAY_TIME_ZONE = 'America/Phoenix';

function formatArizonaTime(date) {
    return date.toLocaleString('en-US', {
        timeZone: DISPLAY_TIME_ZONE,
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short'
    });
}

// Initialize map
function initMap() {
    map = L.map('map').setView(defaultCoords, 2);

    // Keep label tiles above the basemap but below polylines/markers
    map.createPane('labels');
    map.getPane('labels').style.zIndex = 350;
    map.getPane('labels').style.pointerEvents = 'none';

    // Esri Light Gray Canvas: free, no API key, grayscale basemap suited to e-ink
    // (CARTO Positron now requires an API key and shows "API KEY REQUIRED" without one)
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; <a href="https://www.esri.com/">Esri</a> &mdash; Esri, DeLorme, NAVTEQ',
        maxZoom: 16,
        maxNativeZoom: 16
    }).addTo(map);

    // Place labels / boundaries on top of the base canvas
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 16,
        maxNativeZoom: 16,
        opacity: 0.95,
        pane: 'labels'
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
            <circle cx="30" cy="30" r="26" fill="#ffffff" stroke="#BC002D" stroke-width="2.5" opacity="0.95"/>
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
    
    // Center map on ship
    map.setView([lat, lon], 5);
    
    // Update info panel
    updateInfoPanel(locationData);
    
    // Update history trail if it exists
    if (historyData.length > 0) {
        updateHistoryTrail();
    }
}

// Update info panel
function updateInfoPanel(data) {
    if (data.timestamp) {
        const date = new Date(data.timestamp);
        document.getElementById('lastUpdated').textContent = formatArizonaTime(date);
    }
    
    document.getElementById('originCity').textContent = 
        data.origin_city || '-';
    document.getElementById('locationText').textContent = 
        data.location_text || 'Unknown';
    
    // Calculate days until ETA (December 16th, 2025)
    const etaDate = new Date('2025-12-16T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    etaDate.setHours(0, 0, 0, 0);
    const daysUntil = Math.ceil((etaDate - today) / (1000 * 60 * 60 * 24));
    document.getElementById('eta').textContent = 
        daysUntil >= 0 ? `${daysUntil} days` : 'Arrived';
    
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
            // Refresh history trail to ensure it's up to date
            fetchHistory();
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
            // Store history data globally
            historyData = data.history;
            
            // Add header row
            const headerItem = document.createElement('div');
            headerItem.className = 'history-item history-header-row';
            headerItem.innerHTML = `
                <span class="time">Time (MST)</span>
                <span class="origin">Origin</span>
                <span class="destination">Destination</span>
                <span class="coords">Coordinates</span>
            `;
            // Prevent header from being clickable
            headerItem.addEventListener('click', (e) => {
                e.stopPropagation();
            });
            historyList.appendChild(headerItem);
            
            data.history.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                
                const date = new Date(item.timestamp);
                const timeStr = formatArizonaTime(date);
                
                historyItem.innerHTML = `
                    <span class="time">${timeStr}</span>
                    <span class="origin">${item.origin_city || '-'}</span>
                    <span class="destination">${item.location_text || '-'}</span>
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
            
            // Update history trail on map
            updateHistoryTrail();
        } else {
            historyList.innerHTML = '<p style="text-align: center; color: #5A6570;">No history available</p>';
            historyData = [];
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

// Clear history trail from map
function clearHistoryTrail() {
    // Remove all history markers
    historyMarkers.forEach(marker => {
        map.removeLayer(marker);
    });
    historyMarkers = [];
    
    // Remove all history lines
    historyLines.forEach(line => {
        map.removeLayer(line);
    });
    historyLines = [];
}

// Update history trail on map
function updateHistoryTrail() {
    // Clear existing trail
    clearHistoryTrail();
    
    // Check if toggle is enabled
    const toggleCheckbox = document.getElementById('historyTrailToggle');
    if (!toggleCheckbox || !toggleCheckbox.checked) {
        return;
    }
    
    // Get locations with valid coordinates
    if (!historyData || historyData.length === 0) {
        return;
    }
    
    // Get last 50 locations (most recent 50)
    const last50Locations = historyData.slice(0, 50).filter(item => 
        item.latitude && item.longitude
    );
    
    if (last50Locations.length === 0) {
        return;
    }
    
    // Draw markers for each historical location
    last50Locations.forEach((item, index) => {
        const lat = item.latitude;
        const lon = item.longitude;
        
        // Create a small black dot marker
        const historyMarkerIcon = L.divIcon({
            className: 'history-marker',
            html: '',
            iconSize: [10, 10],
            iconAnchor: [5, 5]
        });
        
        const historyMarker = L.marker([lat, lon], { 
            icon: historyMarkerIcon,
            zIndexOffset: -1000
        }).addTo(map);
        
        historyMarkers.push(historyMarker);
    });
    
    // Draw lines connecting consecutive locations (from oldest to newest)
    // Note: historyData is ordered from newest to oldest, so we reverse for the trail
    const reversedLocations = [...last50Locations].reverse();
    
    for (let i = 0; i < reversedLocations.length - 1; i++) {
        const fromLocation = reversedLocations[i];
        const toLocation = reversedLocations[i + 1];
        
        // Draw line from older location to newer location
        const line = L.polyline(
            [[fromLocation.latitude, fromLocation.longitude], 
             [toLocation.latitude, toLocation.longitude]],
            {
                color: '#BC002D',
                weight: 3,
                opacity: 0.75,
                dashArray: '10, 10'
            }
        ).addTo(map);
        
        historyLines.push(line);
    }
}

// Toggle history trail visibility
function toggleHistoryTrail() {
    const isChecked = document.getElementById('historyTrailToggle').checked;
    
    if (isChecked) {
        updateHistoryTrail();
    } else {
        clearHistoryTrail();
    }
}

// Toggle history panel
function toggleHistory() {
    const historyList = document.getElementById('historyList');
    const historyHeader = document.getElementById('historyHeader');
    const collapseIcon = historyHeader.querySelector('.collapse-icon');
    
    historyList.classList.toggle('collapsed');
    
    if (historyList.classList.contains('collapsed')) {
        collapseIcon.textContent = '▼';
    } else {
        collapseIcon.textContent = '▲';
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
    document.getElementById('historyHeader').addEventListener('click', toggleHistory);
    document.getElementById('historyTrailToggle').addEventListener('change', toggleHistoryTrail);
    
    // Auto-refresh every 5 minutes
    setInterval(fetchLocation, 5 * 60 * 1000);
});
