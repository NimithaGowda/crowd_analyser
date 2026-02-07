from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import sqlite3
import json
import random
from datetime import datetime, timedelta
import pandas as pd
import time
import threading

app = Flask(__name__)
CORS(app)

# Database connection
def get_db_connection():
    conn = sqlite3.connect('crowd_mobility.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_database():
    try:
        # Just check if database exists, create_database.py should be run separately
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if len(tables) == 0:
            print("⚠️ Database is empty. Please run create_database.py first")
        else:
            print(f"✅ Database initialized with {len(tables)} tables")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Real-time metrics
@app.route('/api/realtime-metrics')
def get_realtime_metrics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get latest crowd data
    cursor.execute('''
        SELECT AVG(density) as avg_density, 
               COUNT(CASE WHEN anomaly = 1 THEN 1 END) as anomalies,
               COUNT(*) as total_readings
        FROM crowd_data 
        WHERE timestamp > datetime('now', '-5 minutes')
    ''')
    crowd_stats = cursor.fetchone()
    
    # Get latest mobility data
    cursor.execute('''
        SELECT COUNT(DISTINCT vehicle_type) as vehicle_types,
               SUM(co2_emission) as total_co2,
               COUNT(*) as trips
        FROM mobility_data 
        WHERE timestamp > datetime('now', '-5 minutes')
    ''')
    mobility_stats = cursor.fetchone()
    
    # Get latest carbon data
    cursor.execute('''
        SELECT AVG(co2_level) as avg_co2,
               COUNT(*) as readings
        FROM carbon_data 
        WHERE timestamp > datetime('now', '-5 minutes')
    ''')
    carbon_stats = cursor.fetchone()
    
    conn.close()
    
    # Calculate metrics
    crowd_density = round((crowd_stats['avg_density'] or 0.5) * 100, 1)
    anomalies = crowd_stats['anomalies'] or 0
    vehicle_count = mobility_stats['vehicle_types'] or 5
    total_co2 = round(mobility_stats['total_co2'] or 25.5, 2)
    avg_co2 = round(carbon_stats['avg_co2'] or 450, 1)
    
    # Determine status
    crowd_status = 'high' if crowd_density > 70 else 'normal'
    co2_status = 'high' if avg_co2 > 500 else 'normal'
    
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'crowd': {
            'density': crowd_density,
            'anomalies': anomalies,
            'readings': crowd_stats['total_readings'] or 10,
            'status': crowd_status
        },
        'mobility': {
            'vehicle_types': vehicle_count,
            'total_co2': total_co2,
            'trips': mobility_stats['trips'] or 15,
            'status': 'busy' if total_co2 > 30 else 'normal'
        },
        'carbon': {
            'level': avg_co2,
            'readings': carbon_stats['readings'] or 8,
            'status': co2_status
        }
    }
    
    return jsonify(metrics)

# Live graph data
@app.route('/api/live-graph')
def get_live_graph():
    minutes = request.args.get('minutes', 30, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Generate time points
    times = []
    crowd_data = []
    co2_data = []
    
    for i in range(minutes, 0, -5):
        time_point = datetime.now() - timedelta(minutes=i)
        time_str = time_point.strftime('%H:%M')
        
        # Simulate crowd data
        base_density = 50 + random.uniform(-20, 20)
        if 8 <= time_point.hour <= 10 or 17 <= time_point.hour <= 20:
            base_density += random.uniform(10, 30)
        
        # Simulate CO2 data
        base_co2 = 25 + random.uniform(-10, 10)
        if 8 <= time_point.hour <= 10 or 17 <= time_point.hour <= 20:
            base_co2 += random.uniform(5, 15)
        
        times.append(time_str)
        crowd_data.append(max(0, min(100, base_density)))
        co2_data.append(max(0, base_co2))
    
    # Get vehicle distribution
    cursor.execute('''
        SELECT vehicle_type, COUNT(*) as count
        FROM mobility_data 
        WHERE timestamp > datetime('now', '-1 hour')
        GROUP BY vehicle_type
    ''')
    
    vehicle_dist = []
    for row in cursor.fetchall():
        vehicle_dist.append({
            'vehicle': row['vehicle_type'],
            'count': row['count']
        })
    
    # If no real data, add sample data
    if not vehicle_dist:
        vehicle_dist = [
            {'vehicle': 'Car', 'count': 25},
            {'vehicle': 'Bus', 'count': 15},
            {'vehicle': 'EV', 'count': 10},
            {'vehicle': 'Bike', 'count': 8},
            {'vehicle': 'Metro', 'count': 12}
        ]
    
    conn.close()
    
    return jsonify({
        'crowd_graph': [{'time': t, 'density': d} for t, d in zip(times, crowd_data)],
        'co2_graph': [{'time': t, 'co2': c} for t, c in zip(times, co2_data)],
        'vehicle_distribution': vehicle_dist,
        'time_range': minutes
    })

# Daily trends
@app.route('/api/daily-trends')
def get_daily_trends():
    days = request.args.get('days', 7, type=int)
    
    # Generate daily trend data
    days_list = []
    for i in range(days, -1, -1):
        day = datetime.now() - timedelta(days=i)
        days_list.append(day.strftime('%Y-%m-%d'))
    
    # Generate crowd trends by hour
    crowd_trends = []
    for hour in range(24):
        base_density = 40 + random.uniform(-10, 10)
        if 8 <= hour <= 10:
            base_density += 20
        elif 17 <= hour <= 20:
            base_density += 25
        
        crowd_trends.append({
            'hour': hour,
            'density': max(0, min(100, base_density))
        })
    
    # Generate mobility trends
    mobility_trends = {}
    for day in days_list:
        mobility_trends[day] = [
            {'vehicle_type': 'Car', 'trips': random.randint(20, 40)},
            {'vehicle_type': 'Bus', 'trips': random.randint(15, 30)},
            {'vehicle_type': 'EV', 'trips': random.randint(10, 25)},
            {'vehicle_type': 'Bike', 'trips': random.randint(5, 20)}
        ]
    
    return jsonify({
        'crowd_trends': crowd_trends,
        'mobility_trends': mobility_trends,
        'days': days
    })

# Location data
@app.route('/api/location-data')
def get_location_data():
    locations = [
        {"name": "Stadium Main Gate", "density": random.randint(60, 90), "anomalies": random.randint(0, 2), 
         "lat": 12.9784, "lng": 77.5994, "status": "high"},
        {"name": "Parking Lot A", "density": random.randint(40, 70), "anomalies": random.randint(0, 1), 
         "lat": 12.9778, "lng": 77.6003, "status": "medium"},
        {"name": "Metro Station", "density": random.randint(50, 80), "anomalies": random.randint(0, 1), 
         "lat": 12.9780, "lng": 77.6010, "status": "medium"},
        {"name": "Bus Terminal", "density": random.randint(55, 85), "anomalies": random.randint(0, 2), 
         "lat": 12.9795, "lng": 77.5995, "status": "high"},
        {"name": "Food Court", "density": random.randint(30, 60), "anomalies": 0, 
         "lat": 12.9782, "lng": 77.5985, "status": "low"}
    ]
    
    return jsonify(locations)

# Alerts
@app.route('/api/alerts')
def get_alerts():
    alerts = []
    
    # Generate some random alerts
    if random.random() > 0.3:
        alerts.append({
            'type': 'high_density',
            'location': 'Stadium Main Gate',
            'value': random.randint(75, 95),
            'timestamp': datetime.now().isoformat(),
            'priority': 'high'
        })
    
    if random.random() > 0.5:
        alerts.append({
            'type': 'anomaly',
            'location': random.choice(['Parking Lot A', 'Metro Station']),
            'timestamp': datetime.now().isoformat(),
            'priority': 'medium'
        })
    
    if random.random() > 0.7:
        alerts.append({
            'type': 'high_co2',
            'location': 'Bus Terminal',
            'value': random.randint(520, 600),
            'timestamp': datetime.now().isoformat(),
            'priority': 'medium'
        })
    
    return jsonify(alerts)

# System status
@app.route('/api/system-status')
def get_system_status():
    status = {
        'database': {
            'status': 'online',
            'last_update': datetime.now().isoformat(),
            'freshness_minutes': random.randint(0, 2)
        },
        'data_streams': {
            'crowd': {'status': 'active', 'updates_per_hour': random.randint(45, 60)},
            'mobility': {'status': 'active', 'updates_per_hour': random.randint(30, 45)}
        },
        'alerts': {
            'active_alerts': random.randint(0, 3),
            'status': 'normal'
        },
        'overall_status': 'healthy'
    }
    
    return jsonify(status)

# Historical analysis
@app.route('/api/historical-analysis')
def get_historical_analysis():
    days = request.args.get('days', 30, type=int)
    
    # Generate daily data
    daily_data = []
    for i in range(days, -1, -1):
        day = datetime.now() - timedelta(days=i)
        daily_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'crowd_density': 50 + random.uniform(-15, 15),
            'co2_level': 450 + random.uniform(-50, 50),
            'vehicle_diversity': random.randint(4, 7)
        })
    
    # Generate hourly patterns
    hourly_data = []
    for hour in range(24):
        base_density = 40 + random.uniform(-10, 10)
        if 8 <= hour <= 10:
            base_density += 25
        elif 17 <= hour <= 20:
            base_density += 30
        
        hourly_data.append({
            'hour': hour,
            'crowd_density': max(0, min(100, base_density)),
            'co2_level': 400 + random.uniform(-50, 50) + (25 if 8 <= hour <= 10 or 17 <= hour <= 20 else 0)
        })
    
    return jsonify({
        'daily_trends': daily_data,
        'hourly_patterns': hourly_data,
        'analysis_period': days
    })

# Health check
@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Real-time stream
@app.route('/stream')
def stream():
    def event_stream():
        while True:
            # Generate real-time data
            data = {
                'timestamp': datetime.now().isoformat(),
                'crowd': [{
                    'location': random.choice(['Main Gate', 'Parking Lot', 'Metro Station']),
                    'density': random.uniform(0.4, 0.9),
                    'timestamp': datetime.now().isoformat()
                }],
                'mobility': [{
                    'vehicle_type': random.choice(['Car', 'Bus', 'EV']),
                    'co2_emission': random.uniform(1, 5),
                    'timestamp': datetime.now().isoformat()
                }]
            }
            
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(5)  # Send data every 5 seconds
    
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    print("🚀 Starting Crowd Mobility Analyzer...")
    init_database()
    print("🌐 Server starting on http://127.0.0.1:5000")
    print("📡 Real-time dashboard available")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)