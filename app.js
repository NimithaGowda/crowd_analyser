// Global variables
let eventSource;
let map;
let charts = {};
let realtimeData = [];
let updateInterval;

// Chart colors
const chartColors = {
    primary: '#4361ee',
    secondary: '#3a0ca3',
    success: '#4cc9f0',
    warning: '#f72585',
    danger: '#7209b7',
    light: '#adb5bd',
    dark: '#212529'
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Real-Time Crowd Mobility Analyzer...');
    
    // Initialize components
    initMap();
    initCharts();
    initRealTimeConnection();
    loadInitialData();
    updateTime();
    
    // Start periodic updates
    updateInterval = setInterval(updateTime, 1000);
    
    // Load historical analysis
    loadHistoricalAnalysis();
    
    // Set up event listeners
    document.getElementById('time-range').addEventListener('change', updateCharts);
});

// Initialize Leaflet map
function initMap() {
    map = L.map('map').setView([12.9784, 77.5994], 15);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
}

// Initialize charts
function initCharts() {
    // Live trend chart
    const liveCtx = document.getElementById('live-trend-chart').getContext('2d');
    charts.liveTrend = new Chart(liveCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Crowd Density (%)',
                    data: [],
                    borderColor: chartColors.primary,
                    backgroundColor: chartColors.primary + '20',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'CO₂ Emissions (kg)',
                    data: [],
                    borderColor: chartColors.warning,
                    backgroundColor: chartColors.warning + '20',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'minute'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Crowd Density (%)'
                    },
                    min: 0,
                    max: 100
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'CO₂ (kg)'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            },
            animation: {
                duration: 0
            }
        }
    });
    
    // Vehicle distribution chart
    const vehicleCtx = document.getElementById('vehicle-chart').getContext('2d');
    charts.vehicle = new Chart(vehicleCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    chartColors.primary,
                    chartColors.secondary,
                    chartColors.success,
                    chartColors.warning,
                    chartColors.danger,
                    chartColors.light
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
    
    // Daily trend chart
    const dailyCtx = document.getElementById('daily-trend-chart').getContext('2d');
    charts.daily = new Chart(dailyCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Crowd Density',
                    data: [],
                    backgroundColor: chartColors.primary + '80',
                    borderColor: chartColors.primary,
                    borderWidth: 1
                },
                {
                    label: 'CO₂ Level',
                    data: [],
                    backgroundColor: chartColors.warning + '80',
                    borderColor: chartColors.warning,
                    borderWidth: 1,
                    type: 'line',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Crowd Density (%)'
                    }
                },
                y1: {
                    position: 'right',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'CO₂ (ppm)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
    
    // Mini charts
    charts.crowdMini = createMiniChart('crowd-mini-chart', chartColors.primary);
    charts.co2Mini = createMiniChart('co2-mini-chart', chartColors.warning);
}

// Create mini chart
function createMiniChart(canvasId, color) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: 10}, (_, i) => i),
            datasets: [{
                data: Array(10).fill(50),
                borderColor: color,
                borderWidth: 2,
                fill: false,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false,
                    min: 0,
                    max: 100
                }
            },
            elements: {
                point: {
                    radius: 0
                }
            }
        }
    });
}

// Initialize real-time connection
function initRealTimeConnection() {
    eventSource = new EventSource('/stream');
    
    eventSource.onopen = function() {
        console.log('✅ Real-time connection established');
        updateLiveIndicator('connected');
    };
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleRealTimeData(data);
    };
    
    eventSource.onerror = function() {
        console.log('❌ Real-time connection lost');
        updateLiveIndicator('disconnected');
        
        // Try to reconnect after 5 seconds
        setTimeout(initRealTimeConnection, 5000);
    };
}

// Handle real-time data
function handleRealTimeData(data) {
    realtimeData.unshift(data);
    if (realtimeData.length > 100) {
        realtimeData.pop();
    }
    
    // Update data points counter
    document.getElementById('data-points').textContent = 
        `Data points: ${realtimeData.length}`;
    
    // Update metrics
    updateMetrics(data);
    
    // Update charts
    updateLiveCharts(data);
}

// Load initial data
async function loadInitialData() {
    try {
        // Load real-time metrics
        const metrics = await fetch('/api/realtime-metrics').then(r => r.json());
        updateMetrics(metrics);
        
        // Load live graph data
        const liveData = await fetch('/api/live-graph').then(r => r.json());
        updateLiveGraphs(liveData);
        
        // Load location data
        const locations = await fetch('/api/location-data').then(r => r.json());
        updateMap(locations);
        
        // Load alerts
        const alerts = await fetch('/api/alerts').then(r => r.json());
        updateAlerts(alerts);
        
        // Load system status
        const status = await fetch('/api/system-status').then(r => r.json());
        updateSystemStatus(status);
        
        // Load daily trends
        const trends = await fetch('/api/daily-trends').then(r => r.json());
        updateDailyTrends(trends);
        
    } catch (error) {
        console.error('Error loading initial data:', error);
    }
}

// Update metrics display
function updateMetrics(data) {
    if (data.crowd) {
        document.getElementById('crowd-density').textContent = 
            `${data.crowd.density}%`;
        document.getElementById('crowd-status').textContent = 
            data.crowd.status === 'high' ? 'High' : 'Normal';
        document.getElementById('crowd-status').className = 
            `text-${data.crowd.status === 'high' ? 'danger' : 'success'}`;
        
        // Update mini chart
        updateMiniChart(charts.crowdMini, data.crowd.density);
    }
    
    if (data.mobility) {
        document.getElementById('co2-emissions').textContent = 
            `${data.mobility.total_co2} kg`;
        document.getElementById('co2-status').textContent = 
            data.mobility.status === 'busy' ? 'High' : 'Normal';
        document.getElementById('co2-status').className = 
            `text-${data.mobility.status === 'busy' ? 'danger' : 'success'}`;
        
        document.getElementById('active-vehicles').textContent = 
            data.mobility.vehicle_types;
        document.getElementById('traffic-status').textContent = 
            data.mobility.status === 'busy' ? 'Busy' : 'Normal';
        
        // Update mini chart
        updateMiniChart(charts.co2Mini, (data.mobility.total_co2 / 100) * 100);
    }
    
    if (data.carbon) {
        // Update sustainability score
        const score = calculateSustainabilityScore(data);
        document.getElementById('sustainability-score').textContent = score;
        document.getElementById('sustainability-progress').style.width = `${score}%`;
    }
}

// Update mini chart
function updateMiniChart(chart, value) {
    const data = chart.data.datasets[0].data;
    data.shift();
    data.push(value);
    chart.update('none');
}

// Update live charts
function updateLiveCharts(data) {
    const timestamp = new Date(data.timestamp);
    const timeLabel = timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    // Update live trend chart
    const trendChart = charts.liveTrend;
    const labels = trendChart.data.labels;
    const crowdData = trendChart.data.datasets[0].data;
    const co2Data = trendChart.data.datasets[1].data;
    
    labels.push(timeLabel);
    crowdData.push(data.crowd?.density || 0);
    co2Data.push(data.mobility?.total_co2 || 0);
    
    // Keep only last 20 points
    if (labels.length > 20) {
        labels.shift();
        crowdData.shift();
        co2Data.shift();
    }
    
    trendChart.update('none');
}

// Update live graphs from API
async function updateLiveGraphs(liveData) {
    // Update crowd graph
    const crowdGraph = liveData.crowd_graph || [];
    const labels = crowdGraph.map(d => d.time);
    const crowdData = crowdGraph.map(d => d.density);
    const co2Data = liveData.co2_graph.map(d => d.co2);
    
    charts.liveTrend.data.labels = labels;
    charts.liveTrend.data.datasets[0].data = crowdData;
    charts.liveTrend.data.datasets[1].data = co2Data;
    charts.liveTrend.update();
    
    // Update vehicle distribution
    const vehicleDist = liveData.vehicle_distribution || [];
    charts.vehicle.data.labels = vehicleDist.map(d => d.vehicle);
    charts.vehicle.data.datasets[0].data = vehicleDist.map(d => d.count);
    charts.vehicle.update();
}

// Update map with location data
function updateMap(locations) {
    // Clear existing markers
    map.eachLayer(function(layer) {
        if (layer instanceof L.Marker || layer instanceof L.Circle) {
            map.removeLayer(layer);
        }
    });
    
    // Add new markers
    locations.forEach(location => {
        const color = location.status === 'high' ? '#f72585' : 
                     location.status === 'medium' ? '#ff9e00' : '#4cc9f0';
        
        const circle = L.circleMarker([location.lat, location.lng], {
            radius: 15 + (location.density / 5),
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.7
        }).addTo(map);
        
        circle.bindPopup(`
            <strong>${location.name}</strong><br>
            Density: ${location.density}%<br>
            Status: ${location.status.toUpperCase()}<br>
            Anomalies: ${location.anomalies}<br>
            Readings: ${location.readings}
        `);
    });
}

// Update alerts
function updateAlerts(alerts) {
    const container = document.getElementById('alerts-container');
    container.innerHTML = '';
    
    document.getElementById('active-alerts').textContent = `Alerts: ${alerts.length}`;
    
    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-check-circle text-success" style="font-size: 2rem;"></i>
                <p class="mt-2 text-muted">No active alerts</p>
            </div>
        `;
        return;
    }
    
    alerts.forEach(alert => {
        const priorityClass = alert.priority === 'high' ? 'high' : 
                            alert.priority === 'medium' ? 'medium' : 'low';
        
        const icon = alert.type === 'high_density' ? 'bi-people-fill' :
                    alert.type === 'anomaly' ? 'bi-exclamation-triangle-fill' :
                    alert.type === 'high_co2' ? 'bi-cloud-fill' : 'bi-bell-fill';
        
        const alertTime = new Date(alert.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert-item ${priorityClass}`;
        alertElement.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <div class="d-flex align-items-center mb-1">
                        <i class="bi ${icon} me-2"></i>
                        <strong>${getAlertTitle(alert.type)}</strong>
                    </div>
                    <p class="mb-1 small">${alert.location}</p>
                    ${alert.value ? `<small>Value: ${alert.value}</small><br>` : ''}
                    <small class="text-muted">${alertTime}</small>
                </div>
                <span class="badge bg-${alert.priority === 'high' ? 'danger' : 'warning'}">
                    ${alert.priority}
                </span>
            </div>
        `;
        
        container.appendChild(alertElement);
    });
}

// Update system status
function updateSystemStatus(status) {
    const freshness = status.database.freshness_minutes || 0;
    document.getElementById('data-freshness').textContent = 
        `Data: ${freshness} min ago`;
    document.getElementById('data-freshness').className = 
        `badge ${freshness < 2 ? 'bg-success' : freshness < 5 ? 'bg-warning' : 'bg-danger'} me-2`;
    
    document.getElementById('system-status').textContent = 
        `System: ${status.overall_status}`;
    document.getElementById('system-status').className = 
        `badge ${status.overall_status === 'healthy' ? 'bg-success' : 'bg-danger'} me-2`;
}

// Update daily trends
function updateDailyTrends(trends) {
    const crowdTrends = trends.crowd_trends || [];
    const labels = crowdTrends.map(t => `${t.hour}:00`);
    const crowdData = crowdTrends.map(t => t.density);
    
    charts.daily.data.labels = labels;
    charts.daily.data.datasets[0].data = crowdData;
    charts.daily.update();
}

// Load historical analysis
async function loadHistoricalAnalysis() {
    const days = document.getElementById('analysis-days').value;
    
    try {
        const response = await fetch(`/api/historical-analysis?days=${days}`);
        const data = await response.json();
        
        updateHistoricalChart(data);
    } catch (error) {
        console.error('Error loading historical analysis:', error);
    }
}

// Update historical chart
function updateHistoricalChart(data) {
    const historicalCtx = document.getElementById('historical-chart').getContext('2d');
    
    if (charts.historical) {
        charts.historical.destroy();
    }
    
    const dailyData = data.daily_trends || [];
    const labels = dailyData.map(d => d.date.substring(5)); // Remove year
    
    charts.historical = new Chart(historicalCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Crowd Density (%)',
                    data: dailyData.map(d => d.crowd_density),
                    borderColor: chartColors.primary,
                    backgroundColor: chartColors.primary + '20',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'CO₂ Level (ppm)',
                    data: dailyData.map(d => d.co2_level),
                    borderColor: chartColors.warning,
                    backgroundColor: chartColors.warning + '20',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Crowd Density (%)'
                    }
                },
                y1: {
                    position: 'right',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'CO₂ (ppm)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// Update charts based on time range
async function updateCharts() {
    const minutes = document.getElementById('time-range').value;
    
    try {
        const response = await fetch(`/api/live-graph?minutes=${minutes}`);
        const data = await response.json();
        updateLiveGraphs(data);
    } catch (error) {
        console.error('Error updating charts:', error);
    }
}

// Load real-time data manually
async function loadRealTimeData() {
    try {
        const response = await fetch('/api/realtime-metrics');
        const data = await response.json();
        updateMetrics(data);
        
        updateLiveIndicator('refreshed');
        setTimeout(() => updateLiveIndicator('connected'), 1000);
    } catch (error) {
        console.error('Error loading real-time data:', error);
        updateLiveIndicator('error');
    }
}

// Update time display
function updateTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = 
        now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
}

// Update live indicator
function updateLiveIndicator(status) {
    const indicator = document.getElementById('live-indicator');
    
    switch(status) {
        case 'connected':
            indicator.className = 'badge bg-success';
            indicator.textContent = 'LIVE';
            break;
        case 'disconnected':
            indicator.className = 'badge bg-danger';
            indicator.textContent = 'OFFLINE';
            break;
        case 'refreshed':
            indicator.className = 'badge bg-warning';
            indicator.textContent = 'UPDATING';
            break;
        case 'error':
            indicator.className = 'badge bg-danger';
            indicator.textContent = 'ERROR';
            break;
    }
}

// Helper functions
function getAlertTitle(type) {
    const titles = {
        'high_density': 'High Crowd Density',
        'anomaly': 'Crowd Anomaly',
        'high_co2': 'High CO₂ Level'
    };
    return titles[type] || 'Alert';
}

function calculateSustainabilityScore(data) {
    let score = 80; // Base score
    
    // Adjust based on conditions
    if (data.crowd?.status === 'high') score -= 10;
    if (data.mobility?.status === 'busy') score -= 10;
    if (data.carbon?.status === 'high') score -= 10;
    
    // Random variation
    score += Math.random() * 10 - 5;
    
    // Clamp between 0 and 100
    return Math.max(0, Math.min(100, Math.round(score)));
}

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (eventSource) {
        eventSource.close();
    }
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});