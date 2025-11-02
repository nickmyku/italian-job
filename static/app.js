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
    if (!locationData || !locationData.latitude || !locationData.longitude) {
        showStatus('No location data available', 'error');
        return;
    }
    
    const lat = locationData.latitude;
    const lon = locationData.longitude;
    
    // Remove existing marker
    if (shipMarker) {
        map.removeLayer(shipMarker);
    }
    
    // Create custom ship icon
    const shipIcon = L.divIcon({
        className: 'ship-marker',
        html: '<div style="font-size: 30px;">??</div>',
        iconSize: [40, 40],
        iconAnchor: [20, 20]
    });
    
    // Add marker
    shipMarker = L.marker([lat, lon], { icon: shipIcon }).addTo(map);
    
    // Create popup content
    let popupContent = `<strong>Sagittarius Leader</strong><br>`;
    if (locationData.location_text) {
        popupContent += `Location: ${locationData.location_text}<br>`;
    }
    popupContent += `Coordinates: ${lat.toFixed(6)}, ${lon.toFixed(6)}<br>`;
    if (locationData.speed) {
        popupContent += `Speed: ${locationData.speed} knots<br>`;
    }
    if (locationData.heading) {
        popupContent += `Heading: ${locationData.heading}?`;
    }
    
    shipMarker.bindPopup(popupContent).openPopup();
    
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
        data.heading ? `${data.heading}?` : '-';
    
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
            showStatus('Location updated successfully', 'success');
        } else {
            showStatus('No location data found', 'error');
        }
    } catch (error) {
        console.error('Error fetching location:', error);
        showStatus('Error loading location', 'error');
    }
}

// Manual update
async function manualUpdate() {
    try {
        showStatus('Updating location...', 'loading');
        const response = await fetch('/api/update', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            updateMap(data.data);
            showStatus('Location updated successfully', 'success');
            // Refresh history
            fetchHistory();
        } else {
            showStatus('Failed to update location: ' + (data.message || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error updating location:', error);
        showStatus('Error updating location', 'error');
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
