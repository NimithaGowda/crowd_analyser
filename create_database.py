import sqlite3
import random
from datetime import datetime, timedelta
import time
import threading
import sys

def create_crowd_mobility_db():
    print("🚀 Creating crowd_mobility.db database...")
    
    conn = sqlite3.connect('crowd_mobility.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    print("📊 Creating fresh tables...")
    cursor.execute('DROP TABLE IF EXISTS crowd_data')
    cursor.execute('DROP TABLE IF EXISTS mobility_data')
    cursor.execute('DROP TABLE IF EXISTS carbon_data')
    
    # Create tables with proper schema
    cursor.execute('''
    CREATE TABLE crowd_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT NOT NULL,
        density REAL NOT NULL,
        timestamp DATETIME NOT NULL,
        anomaly INTEGER DEFAULT 0,
        emotion_score REAL DEFAULT 0.5,
        category TEXT DEFAULT 'normal'
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE mobility_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_type TEXT NOT NULL,
        route TEXT NOT NULL,
        co2_emission REAL NOT NULL,
        distance REAL NOT NULL,
        timestamp DATETIME NOT NULL,
        speed REAL DEFAULT 30.0,
        status TEXT DEFAULT 'moving'
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE carbon_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT NOT NULL,
        co2_level REAL NOT NULL,
        timestamp DATETIME NOT NULL,
        source TEXT NOT NULL,
        trend TEXT DEFAULT 'stable'
    )
    ''')
    
    conn.commit()
    print("✅ Database structure created")
    
    # Generate initial historical data
    generate_historical_data(conn, cursor)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_crowd_timestamp ON crowd_data(timestamp)")
    cursor.execute("CREATE INDEX idx_mobility_timestamp ON mobility_data(timestamp)")
    cursor.execute("CREATE INDEX idx_carbon_timestamp ON carbon_data(timestamp)")
    cursor.execute("CREATE INDEX idx_crowd_location ON crowd_data(location)")
    
    conn.commit()
    conn.close()
    print("✅ Database created successfully: crowd_mobility.db")
    
    return True

def generate_historical_data(conn, cursor):
    """Generate 7 days of historical data"""
    print("📅 Generating 7-day historical data...")
    
    locations = [
        "Stadium Main Gate", "Stadium North Stand", "Stadium South Stand",
        "VIP Entrance", "Parking Lot A", "Parking Lot B", "Metro Station",
        "Bus Terminal", "Food Court", "Security Checkpoint"
    ]
    
    vehicle_types = ["Car", "Bus", "EV", "Bike", "Metro", "Walking", "Taxi"]
    routes = ["Route A", "Route B", "Route C", "Route D"]
    sources = ["Transport", "Energy", "Commercial", "Waste"]
    
    # Generate data for last 7 days
    for day_offset in range(7, -1, -1):
        base_date = datetime.now() - timedelta(days=day_offset)
        
        # Generate crowd data for each hour
        for hour in range(24):
            timestamp = base_date.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
            
            # Simulate peak hours (8-10 AM, 5-8 PM)
            is_peak_hour = (8 <= hour <= 10) or (17 <= hour <= 20)
            
            for location in locations:
                # Base density
                base_density = random.uniform(0.1, 0.6)
                
                # Increase during peak hours
                if is_peak_hour:
                    base_density *= random.uniform(1.3, 2.0)
                
                # Location-specific adjustments
                if "Gate" in location or "Entrance" in location:
                    base_density *= random.uniform(1.2, 1.8)
                elif "Parking" in location:
                    base_density *= random.uniform(0.8, 1.2)
                
                density = min(1.0, base_density)
                anomaly = 1 if random.random() < 0.02 else 0
                emotion_score = random.uniform(0.4, 0.9)
                category = 'historical'
                
                cursor.execute('''
                INSERT INTO crowd_data (location, density, timestamp, anomaly, emotion_score, category)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (location, density, timestamp, anomaly, emotion_score, category))
        
        # Generate mobility data
        for _ in range(50):
            vehicle = random.choice(vehicle_types)
            route = random.choice(routes)
            distance = round(random.uniform(1, 25), 2)
            
            # Emission factors
            emission_factors = {
                "Car": 0.2, "Bus": 0.1, "EV": 0.05, "Bike": 0.01,
                "Metro": 0.05, "Walking": 0.0, "Taxi": 0.25
            }
            
            co2_emission = round(emission_factors[vehicle] * distance, 2)
            timestamp = base_date.replace(
                hour=random.randint(0, 23),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            speed = random.uniform(20, 80)
            status = random.choice(['moving', 'idle', 'slow'])
            
            cursor.execute('''
            INSERT INTO mobility_data (vehicle_type, route, co2_emission, distance, timestamp, speed, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (vehicle, route, co2_emission, distance, timestamp, speed, status))
        
        # Generate carbon data
        for _ in range(30):
            location = random.choice(locations)
            source = random.choice(sources)
            
            # Base CO2 levels with daily patterns
            base_co2 = random.uniform(300, 600)
            
            # Increase during peak hours
            hour = random.randint(0, 23)
            if 8 <= hour <= 10 or 17 <= hour <= 20:
                base_co2 *= random.uniform(1.2, 1.5)
            
            co2_level = round(base_co2, 2)
            timestamp = base_date.replace(
                hour=hour,
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            trend = random.choice(['increasing', 'stable', 'decreasing'])
            
            cursor.execute('''
            INSERT INTO carbon_data (location, co2_level, timestamp, source, trend)
            VALUES (?, ?, ?, ?, ?)
            ''', (location, co2_level, timestamp, source, trend))
    
    conn.commit()
    print(f"✅ Generated historical data for 7 days")
    return True

def add_realtime_data():
    """Add real-time data point"""
    try:
        conn = sqlite3.connect('crowd_mobility.db', check_same_thread=False)
        cursor = conn.cursor()
        
        locations = ["Stadium Main Gate", "Parking Lot A", "Metro Station", "Bus Terminal"]
        vehicle_types = ["Car", "Bus", "EV", "Bike", "Taxi"]
        sources = ["Transport", "Energy", "Commercial"]
        
        timestamp = datetime.now()
        
        # Add crowd data
        for location in locations:
            # Simulate real-time variations
            base_hour_factor = 1.0
            current_hour = timestamp.hour
            
            # Peak hours adjustment
            if 8 <= current_hour <= 10:
                base_hour_factor = 1.5
            elif 17 <= current_hour <= 20:
                base_hour_factor = 1.8
            elif 0 <= current_hour <= 5:
                base_hour_factor = 0.4
            
            base_density = random.uniform(0.3, 0.7) * base_hour_factor
            density = min(1.0, base_density)
            
            # Random anomalies
            anomaly = 1 if random.random() < 0.05 else 0
            emotion_score = random.uniform(0.5, 0.9)
            category = 'realtime'
            
            cursor.execute('''
            INSERT INTO crowd_data (location, density, timestamp, anomaly, emotion_score, category)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (location, density, timestamp, anomaly, emotion_score, category))
        
        # Add mobility data
        for _ in range(5):
            vehicle = random.choice(vehicle_types)
            route = f"Route {random.choice(['A', 'B', 'C', 'D'])}"
            distance = round(random.uniform(5, 20), 2)
            
            emission_factors = {
                "Car": 0.2, "Bus": 0.1, "EV": 0.05,
                "Bike": 0.01, "Taxi": 0.25
            }
            
            co2_emission = round(emission_factors[vehicle] * distance, 2)
            speed = random.uniform(20, 60)
            status = random.choice(['moving', 'idle', 'slow'])
            
            cursor.execute('''
            INSERT INTO mobility_data (vehicle_type, route, co2_emission, distance, timestamp, speed, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (vehicle, route, co2_emission, distance, timestamp, speed, status))
        
        # Add carbon data
        for location in locations[:2]:
            source = random.choice(sources)
            
            # Real-time CO2 with variations
            base_co2 = random.uniform(350, 550)
            
            # Time-based adjustments
            if 8 <= current_hour <= 10 or 17 <= current_hour <= 20:
                base_co2 *= 1.3
            
            co2_level = round(base_co2, 2)
            trend = random.choice(['increasing', 'stable', 'decreasing'])
            
            cursor.execute('''
            INSERT INTO carbon_data (location, co2_level, timestamp, source, trend)
            VALUES (?, ?, ?, ?, ?)
            ''', (location, co2_level, timestamp, source, trend))
        
        conn.commit()
        conn.close()
        print(f"✅ Added real-time data at {timestamp.strftime('%H:%M:%S')}")
        return True
    except Exception as e:
        print(f"❌ Error adding real-time data: {e}")
        return False

def start_realtime_updater():
    """Start thread to add real-time data every minute"""
    def update_loop():
        while True:
            try:
                add_realtime_data()
            except Exception as e:
                print(f"❌ Error in update loop: {e}")
            time.sleep(60)  # Update every minute
    
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()
    print("🚀 Real-time data updater started (updates every minute)")
    return thread

if __name__ == "__main__":
    # Create database first
    create_crowd_mobility_db()
    
    # Start real-time updater
    updater_thread = start_realtime_updater()
    
    # Show database stats
    conn = sqlite3.connect('crowd_mobility.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM crowd_data")
    crowd_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM mobility_data")
    mobility_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM carbon_data")
    carbon_count = cursor.fetchone()[0]
    
    print("\n📊 Database Statistics:")
    print(f"   Crowd Data Records: {crowd_count}")
    print(f"   Mobility Data Records: {mobility_count}")
    print(f"   Carbon Data Records: {carbon_count}")
    print(f"   Total Records: {crowd_count + mobility_count + carbon_count}")
    
    conn.close()
    
    # Keep the script running
    print("\n🔄 Real-time data generator is running...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping real-time updater...")
        sys.exit(0)