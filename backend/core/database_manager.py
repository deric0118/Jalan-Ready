import sqlite3
from datetime import datetime
import os
import csv
from dotenv import load_dotenv

class DatabaseManager:
    def __init__(self, db_name=None):
        if db_name is None:
            db_name = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "data", "jalan-ready.db")
            )
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # 1. Core table with LLM Guardrails (CHECK constraint) and auto-timestamps
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                latitude REAL,
                longitude REAL,
                road_name TEXT,
                defect_type TEXT,
                issue_type TEXT,
                confidence REAL,
                urgency_score INTEGER,
                workflow_state TEXT CHECK(workflow_state IN (
                    'NEW', 
                    'AWAITING_INFO', 
                    'REPORTED', 
                    'IN_PROGRESS', 
                    'ESCALATED', 
                    'DELAYED_TRAFFIC',
                    'RESOLVED',
                    'MANUAL_REVIEW'
                )) DEFAULT 'NEW',
                jurisdiction TEXT,
                is_recurring BOOLEAN DEFAULT 0,
                report_count INTEGER DEFAULT 1,
                reasoning_path TEXT,
                image_path TEXT
            )
        ''')
        
        # 2. Trigger to auto-update 'updated_at' on any row modification
        # This is vital for your background engine to track time-in-state (e.g., >48 hours)
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS UpdateLastTime 
            AFTER UPDATE ON reports
            FOR EACH ROW
            BEGIN
                UPDATE reports SET updated_at = CURRENT_TIMESTAMP WHERE id = old.id;
            END;
        ''')
        
        self.conn.commit()

    def get_pending_tasks(self, jurisdiction_filter=None):
        """Fetch all reports ready for contractor action."""
        cursor = self.conn.cursor()
        query = "SELECT * FROM reports WHERE workflow_state = 'REPORTED'"
        params = ()
        if jurisdiction_filter:
            query += " AND jurisdiction = ?"
            params = (jurisdiction_filter,)
        
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def check_historical_recurrence(self, lat, lon, threshold_deg=0.0001):
        """
        Tool D: The Historian.
        Checks for previously RESOLVED reports within a geospatial bounding box.

        :param lat: Latitude of the current detection.
        :param lon: Longitude of the current detection.
        :param threshold_deg: Search radius in degrees (0.0001 ~= 11 meters).
        :return: Dictionary containing details of previous failures for AI Root Cause Analysis.
        """
        try:
            cursor = self.conn.cursor()

            # Define the bounding box for the spatial query
            lat_min, lat_max = lat - threshold_deg, lat + threshold_deg
            lon_min, lon_max = lon - threshold_deg, lon + threshold_deg

            query = '''
                SELECT id, defect_type, updated_at FROM reports 
                WHERE latitude BETWEEN ? AND ? 
                AND longitude BETWEEN ? AND ?
                AND workflow_state = 'RESOLVED'
            '''

            cursor.execute(query, (lat_min, lat_max, lon_min, lon_max))
            rows = cursor.fetchall()

            # If rows exist, format them so the AI can read what failed previously
            if rows:
                history = [{"report_id": r[0], "past_defect_type": r[1], "resolved_date": r[2]} for r in rows]
                return {"has_history": True, "message": "Previous resolved repairs found.", "history_details": history}
            else:
                return {"has_history": False, "message": "No previous repairs found.", "history_details": []}

        except Exception as e:
            print(f"⚠️ [SYSTEM ERROR] Tool D failure: {e}")
            return {"has_history": False, "error": str(e)}

    def get_nearby_active_reports(self, lat: float, lon: float, radius_meters=50) -> list:
        """
        Tool for the AI to fetch nearby tickets and decide if they are duplicates.
        """
        offset = radius_meters / 111000.0 
        
        # FIXED: Explicit direct connection
        conn = sqlite3.connect("data/jalan-ready.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, road_name, defect_type, workflow_state, timestamp 
            FROM reports 
            WHERE workflow_state NOT IN ('RESOLVED', 'REJECTED')
            AND latitude BETWEEN ? AND ?
            AND longitude BETWEEN ? AND ?
        """, (lat - offset, lat + offset, lon - offset, lon + offset))
        
        # Format as a clean dictionary for the AI to read
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        
        return results

    def increment_duplicate_count(self, report_id: str):
        """Adds +1 to the report count of an existing ticket."""
        
        # FIXED: Explicit direct connection
        conn = sqlite3.connect("data/jalan-ready.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE reports 
            SET report_count = report_count + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (report_id,))
        conn.commit()
        conn.close()

    def lookup_jurisdiction_contact(self, district: str, road_type: str) -> dict:
        """
        Tool for the AI to dynamically find the correct authority and email from the CSV.
        Implements a safe testing mechanism (Gmail Alias Trick) using SMTP_USERNAME.
        """
        load_dotenv(override=True)  # Ensure we load the latest .env values, especially in testing environments
        
        csv_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "selangor_jurisdiction.csv")
        )
        
        # Clean inputs for robust matching
        search_district = district.strip().lower()
        search_road_type = road_type.strip().lower()
        
        # Fallback values if nothing matches
        authority = "Unknown Authority"
        raw_email = "aduan@jkr.gov.my"
        
        try:
            with open(csv_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Perform case-insensitive match
                    if search_district in row['district'].lower() and search_road_type in row['road_type'].lower():
                        authority = row['authority']
                        raw_email = row['email']
                        break
        except FileNotFoundError:
            return {"error": f"Jurisdiction CSV not found at {csv_path}"}
            
        # --- THE GMAIL ALIAS SAFETY TRICK ---
        # Automatically pull the username from .env to generate the safe testing alias
        sender_email = os.getenv("SMTP_USERNAME")
        safe_email = raw_email
        
        if sender_email and "@" in sender_email:
            username, domain = sender_email.split("@", 1)
            # Example: target is 'aduan.petalingjkr@gmail.com' -> suffix is 'aduan.petalingjkr'
            alias_suffix = raw_email.split("@")[0] 
            safe_email = f"{username}+{alias_suffix}@{domain}"
            
        return {
            "authority": authority, 
            "real_target_email": raw_email, 
            "safe_dispatch_email": safe_email,
            "note": f"Using alias {safe_email} for safe testing instead of {raw_email}"
        }