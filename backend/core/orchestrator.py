from backend.database_manager import DatabaseManager
from backend.engine_tools import tool_b_route_optimizer, tool_c_user_communicator
from backend.weather_service import WeatherService
from backend.geo_config import determine_jurisdiction # <--- ADDED IMPORT
import json
import sqlite3

class JalanReadyAgent:
    def __init__(self):
        self.db = DatabaseManager()
        self.weather = WeatherService()
        
        self.SYSTEM_PROMPT = """
        You are the Central Reasoning Engine for Jalan-Ready, an autonomous 
        infrastructure governance system for Selangor, Malaysia.

        Your Task: Analyze a 'Context Packet' containing YOLO detection, GPS, 
        Road Name, and Weather.

        Reasoning Rules:
        1. Jurisdiction: If road starts with 'FT', assign to 'JKR Federal'. 
           If starts with 'B', assign to 'JKR State'. 
           Otherwise, assign to the relevant Local Council (e.g., MBPJ, MBSA).
        2. Priority (1-100):
           - Potholes/Cracks = 50 base.
           - Sinkholes/Structural Failure = 90 base.
           - If 'is_recurring' is True, add +30 to priority and flag for 'Structural Audit'.
           - If 'weather' is 'Heavy Rain' and hazard is 'Sinkhole', set to 100.
        
        Output: Return a JSON object with 'urgency_score', 'assigned_authority', 'workflow_state', and 'reasoning_path'.
        """

    def process_new_report(self, perception_data):
        print(f"\n[AGENT] Analyzing Report: {perception_data.get('road_name', 'Unknown Road')}...")
        
        lat = perception_data.get('lat')
        lon = perception_data.get('lon')
        location_name = perception_data.get('location_name', '')
        road_name = perception_data.get('road_name', 'Unknown')
        
        # 1. Resolve Missing GPS Context
        if (lat is None or lon is None) and location_name:
            print(f"🔍 [CONTEXT] Missing GPS. Attempting to resolve: {location_name}")
            lat, lon = self.weather.get_coords_from_name(location_name)
            
            if lat and lon:
                print(f"📍 [GEO] Resolved '{location_name}' to {lat}, {lon}")
                perception_data['lat'] = lat
                perception_data['lon'] = lon

        # 2. Guardrail: Tool C Execution
        workflow_state = 'REPORTED'
        if lat is None or lon is None:
            print("⚠️ [SYSTEM] GPS resolution failed. Triggering Tool C.")
            tool_c_user_communicator("TEMP_ID", "missing_gps")
            workflow_state = 'AWAITING_INFO' # Change state instead of returning immediately
            
        # 3. Autonomous Weather Context Enrichment
        current_weather = perception_data.get('weather')
        if not current_weather and lat and lon:
            current_weather = self.weather.get_weather(lat=lat, lon=lon)
            perception_data['weather'] = current_weather
            print(f"☁️ [CONTEXT] Autonomous Weather Check: {current_weather}")
            
        # 4. Tool D: Check history (only if we have coordinates)
        is_recurring = False
        if lat and lon:
            is_recurring = self.db.check_historical_recurrence(lat, lon)
        
        # 5. GLM Reasoning (Passing location string for spatial mapping)
        urgency, jurisdiction, reasoning_path = self.get_glm_decision(perception_data, is_recurring)

        # 6. Save to Memory (Removed manual timestamp, relying on DB Schema)
        try:
            cursor = self.db.conn.cursor()
            query = '''
            INSERT INTO reports (
                latitude, longitude, road_name, issue_type, 
                confidence, urgency_score, workflow_state, jurisdiction, 
                is_recurring, reasoning_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            values = (
                lat, 
                lon, 
                road_name,
                perception_data.get('yolo_label', 'unknown'), 
                perception_data.get('confidence', 0.0), 
                urgency, 
                workflow_state, 
                jurisdiction, 
                int(is_recurring), 
                reasoning_path
            )
            
            cursor.execute(query, values)
            self.db.conn.commit()
            print(f"✅ [SAVED] ID: {cursor.lastrowid} | State: {workflow_state}")
            print(f"🧠 [REASONING PATH]: {reasoning_path}")
            
        except sqlite3.Error as e:
            print(f"❌ [DB ERROR] Failed to save report: {e}")
            return "STATE: ERROR"
        
        return f"Authority: {jurisdiction} | Urgency: {urgency}/100 | State: {workflow_state}"

    def get_glm_decision(self, data, recurring):
        """
        Mocking the LLM output. Combines Prefix checking with Spatial checking.
        """
        road_name = data.get('road_name', '')
        location_name = data.get('location_name', '')
        issue = data.get('yolo_label', 'pothole')
        weather = data.get('weather', 'Clear')
        
        # Combine strings for better spatial matching
        address_to_check = f"{road_name} {location_name}".strip()
        
        # 1. Jurisdiction Logic (Prefix Check TRUMPS Spatial Mapping)
        if road_name.startswith("FT") or " FT" in road_name:
            jurisdiction = "JKR Federal"
        elif road_name.startswith("B") or " B" in road_name:
            jurisdiction = "JKR State"
        else:
            # Trigger the geo_config.py dictionary check
            jurisdiction = determine_jurisdiction(address_to_check)

        # 2. Mock Reasoning Path
        reasons = [f"Detected {issue}."]
        
        # 3. Mock Priority Logic
        urgency = 90 if "sinkhole" in issue else 50
        if recurring:
            urgency += 30
            reasons.append("Historical failure detected: Escalated to Structural Audit.")
        if weather == "Heavy Rain" and "sinkhole" in issue:
            urgency = 100
            reasons.append("Extreme weather + high risk hazard: Immediate emergency response triggered.")
            
        urgency = min(urgency, 100)
        reasoning_path = " ".join(reasons)

        return urgency, jurisdiction, reasoning_path

    def generate_daily_plan(self, jurisdiction):
        print(f"\n[AGENT] Querying pending tasks for {jurisdiction}...")
        tasks = self.db.get_pending_tasks(jurisdiction)
        
        if not tasks:
            print(f"ℹ️ No pending tasks found for {jurisdiction}.")
            return []

        optimized_plan = tool_b_route_optimizer(tasks)
        return optimized_plan