import sqlite3
try:
    from backend.core.orchestrator import JalanReadyAgent
    from backend.core.database_manager import DatabaseManager
except ModuleNotFoundError:
    from core.orchestrator import JalanReadyAgent
    from core.database_manager import DatabaseManager
import time
import os

DB_NAME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "jalan-ready.db")
)

def inject_historical_data(db_path=DB_NAME):
    """Force a resolved state so Tool D can trigger during the demo."""
    db = DatabaseManager(db_path)
    cursor = db.conn.cursor()
    # Insert a fake resolved report at the Scenario 3 coordinates
    cursor.execute('''
        INSERT INTO reports (timestamp, latitude, longitude, road_name, issue_type, workflow_state)
        VALUES (datetime('now'), 3.125, 101.652, 'B15 Jalan Bangi', 'alligator_cracking', 'RESOLVED')
    ''')
    db.conn.commit()
    db.conn.close()
    print(f"🛠️ [SYSTEM] Historical data injected into {db_path} for Scenario 3.")
    
def run_demo():
    # 1. Setup
    inject_historical_data(DB_NAME) 
    agent = JalanReadyAgent(db_name=DB_NAME)
    
    agent.USE_LIVE_AI = False
    
    scenarios = [
        {
            "desc": "Scenario 1: Standard Federal Road Pothole",
            "data": {
                "lat": 3.125, 
                "lon": 101.652, 
                "road_name": "FT01 Federal Highway", 
                "yolo_label": "pothole", 
                "confidence": 0.95}
        },
        {
            "desc": "Scenario 2: Missing GPS (Triggers Tool C)",
            "data": {"lat": 3.125, 
                     "lon": 101.652, 
                     "road_name": "Unknown", 
                     "yolo_label": "pothole", 
                     "confidence": 0.88}
        },
        {
            "desc": "Scenario 3: Recurring Failure (Triggers Tool D)",
            "data": {"lat": 3.125, 
                     "lon": 101.652, 
                     "road_name": "B15 Jalan Bangi", 
                     "yolo_label": "alligator_cracking", 
                     "confidence": 0.92}
        },    
        {
            "desc": "Scenario 4: Autonomous Geocoding (Name only, no GPS)",
            "data": {
                "location_name": "Klang", 
                "road_name": "Jalan Jambatan Kota", 
                "yolo_label": "pothole", 
                "confidence": 0.50}
        },    
    ]

    print("\n🚀 STARTING JALAN-READY BACKEND DEMO\n" + "="*40)
    
    for s in scenarios:
        print(f"\n[RUNNING] {s['desc']}")
        result = agent.process_new_report(s['data'])
        print(f"[RESULT] {result}")
        time.sleep(1.5)

    # 2. Showcase Tool B (The Winning Feature)
    print("\n" + "="*40)
    print("📋 GENERATING CONTRACTOR DAILY PLAN (TOOL B)")
    print("Target Authority: JKR Federal")
    print("="*40)
    
    plan = agent.generate_daily_plan("JKR Federal")
    
    if not plan:
        print("Empty Plan: No pending high-priority tasks found.")
    else:
        for i, stop in enumerate(plan, 1):
            print(f"📍 STOP {i}: [Priority {stop['urgency']}]")
            print(f"   ROAD  : {stop['road']}")
            print(f"   ISSUE : {stop['issue'].upper()}")
            print(f"   GPS   : {stop['lat']}, {stop['lon']}")
            print(f"   NAV   : https://www.google.com/maps/search/?api=1&query={stop['lat']},{stop['lon']}")
            print("-" * 30)

    print("\n✅ MISSION COMPLETE: Route Optimized for efficiency and urgency.")

if __name__ == "__main__":
    run_demo()