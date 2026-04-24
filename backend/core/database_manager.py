import sqlite3
from datetime import datetime
import os

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
        :return: Boolean indicating if the location has a history of failure.
        """
        try:
            cursor = self.conn.cursor()

            # Define the bounding box for the spatial query
            lat_min, lat_max = lat - threshold_deg, lat + threshold_deg
            lon_min, lon_max = lon - threshold_deg, lon + threshold_deg

            query = '''
                SELECT COUNT(*) FROM reports 
                WHERE latitude BETWEEN ? AND ? 
                AND longitude BETWEEN ? AND ?
                AND workflow_state = 'RESOLVED'
            '''

            cursor.execute(query, (lat_min, lat_max, lon_min, lon_max))
            count = cursor.fetchone()[0]

            # If count > 0, this is a recurring structural issue
            return count > 0

        except Exception as e:
            print(f"⚠️ [SYSTEM ERROR] Tool D failure: {e}")
            return False  # Fail-safe: assume not recurring if DB fails

    def update_workflow_state(self, report_id, new_state, note=None):
        """Update a report's workflow state and optionally append a reasoning note."""
        cursor = self.conn.cursor()
        if note:
            cursor.execute(
                '''
                UPDATE reports
                SET workflow_state = ?,
                    reasoning_path = COALESCE(reasoning_path, '') || ?
                WHERE id = ?
                ''',
                (new_state, f" [{note}]", report_id),
            )
        else:
            cursor.execute(
                "UPDATE reports SET workflow_state = ? WHERE id = ?",
                (new_state, report_id),
            )
        self.conn.commit()