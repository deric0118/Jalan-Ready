import time
import sqlite3
import json
from datetime import datetime, timedelta
import os
import sys

# Import the existing agent to reuse its tool-calling brain!
from backend.core.orchestrator import JalanReadyAgent

DB_PATH = "data/jalan-ready.db"

class BackgroundEngine:
    def __init__(self, demo_mode=True):
        """
        Initializes the Background Cron Engine.
        demo_mode=True compresses 24 hours into 15 seconds for hackathon judging.
        """
        self.demo_mode = demo_mode
        self.delay_threshold = timedelta(seconds=15) if demo_mode else timedelta(hours=24)
        self.agent = JalanReadyAgent()
        
        print(f"🕒 [BACKGROUND ENGINE] Booting up...")
        if self.demo_mode:
            print(f"⚠️ [DEMO MODE ACTIVE] 24-Hour delays compressed to 15 seconds.")

    def _get_db_connection(self):
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        return sqlite3.connect(DB_PATH)

    def run(self):
        """The infinite loop that acts as the system's heartbeat."""
        print("🕒 [BACKGROUND ENGINE] Monitoring database for delayed AWAITING_INFO reports...")
        
        while True:
            self._sweep_database()
            # Print a subtle dot so you know the loop is alive and not stuck
            sys.stdout.write(".")
            sys.stdout.flush()
            # Sleep for 5 seconds before checking the database again
            time.sleep(5)

    def _sweep_database(self):
        """Hunts for tickets delayed by weather that are past their waiting period."""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # 1. Use 'AWAITING_INFO' to respect your DB schema
            # 2. Use 'updated_at' to match your schema
            cursor.execute("SELECT id, road_name, defect_type, updated_at FROM reports WHERE workflow_state = 'AWAITING_INFO'")
            delayed_reports = cursor.fetchall()

            for report in delayed_reports:
                report_id, road_name, defect_type, updated_at_str = report
                
                try:
                    last_updated = datetime.fromisoformat(updated_at_str)
                except (ValueError, TypeError):
                    last_updated = datetime.now() - timedelta(days=2) 

                time_since_delay = datetime.now() - last_updated
                if time_since_delay >= self.delay_threshold:
                    print(f"\n⏰ [ALARM] Buffer period over for Report #{report_id} at {road_name}.")
                    self._re_evaluate_weather(report_id, road_name, defect_type, conn)

            conn.close()
            
        except sqlite3.OperationalError as e:
            # Fails gracefully if the table doesn't exist yet during early testing
            print(f"\n⚠️ [DB WARNING] Could not read database: {e}. Retrying in 5s...")
        except Exception as e:
            print(f"\n⚠️ [SYSTEM ERROR] {e}")

    def _re_evaluate_weather(self, report_id, road_name, defect_type, db_connection):
        """Wakes up the Z.ai GLM to specifically re-check the weather and update the schedule."""
        print(f"🧠 [AGENT WAKEUP] Handing Report #{report_id} back to Z.ai for weather re-evaluation...")
        
        # We write a highly specific sub-prompt just for this task, strictly respecting DB constraints
        system_prompt = """
        You are the Jalan-Ready Scheduling Re-evaluation Agent.
        Your task is to check if a previously weather-delayed road repair can now be scheduled.
        
        You MUST use the `get_weather` or `geocode_location` tools to check the current weather for the provided location.
        
        Rules:
        1. If the rain has stopped and conditions are dry, set workflow_state to 'REPORTED' and output a specific scheduled_time (e.g., 'Today at 2:00 PM').
        2. If it is still raining or rain is highly probable, keep workflow_state as 'AWAITING_INFO' and set scheduled_time to 'Delayed another 24 Hours'.
        
        Output ONLY a JSON object with: 'workflow_state', 'scheduled_time', and 'reasoning_path'.
        """
        
        user_message = f"Please re-evaluate Report #{report_id}. Location: {road_name}. Defect: {defect_type}."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Reuse the existing agent loop from orchestrator.py!
        decision = self.agent._execute_agent_loop(messages)
        
        if "error" not in decision:
            print(f"✅ [AGENT DECISION] {decision.get('reasoning_path')}")
            
            # Update the database with the new status
            new_state = decision.get('workflow_state', 'AWAITING_INFO')
            new_time = datetime.now().isoformat()
            
            # FIXED: Uses updated_at to match your database schema
            cursor = db_connection.cursor()
            cursor.execute("""
                UPDATE reports 
                SET workflow_state = ?, updated_at = ? 
                WHERE id = ?
            """, (new_state, new_time, report_id))
            db_connection.commit()
            
            print(f"🔄 [STATE UPDATE] Report #{report_id} changed to [{new_state}].\n")
        else:
            print(f"⚠️ [AGENT ERROR] Failed to get AI decision: {decision['error']}\n")

if __name__ == "__main__":
    engine = BackgroundEngine(demo_mode=True)
    engine.run()