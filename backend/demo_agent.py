import json
import sqlite3
from backend.core.orchestrator import JalanReadyAgent
from backend.core.database_manager import DatabaseManager

def run_demo():
    agent = JalanReadyAgent()
    db = DatabaseManager()
    
    print("\n🚀 STARTING PURE AGENTIC DEMO\n" + "="*40)
    
    image_path = r"C:\Users\njxnj\Downloads\Telegram Desktop\test_road.jpg"
    location_input = "N3A, Djanet, Algeria"
    
    # We hand it straight to the AI without a Python gatekeeper!
    print("\n--- 🚀 Waking up Z.ai Agent to Orchestrate & Deduplicate ---")
    result = agent.process_new_report(
        image_path=image_path, 
        location_input=location_input 
    )
    
    print("\n--- 🧠 FINAL GLM JSON DECISION ---")
    print(json.dumps(result, indent=2))

    # Act on the AI's Agentic Decision!
    if result.get("is_duplicate"):
        target_id = result.get("duplicate_of_id")
        print(f"\n🛑 [AGENT REASONING] The AI successfully identified this as a duplicate of Report #{target_id}!")
        if target_id:
            db.increment_duplicate_count(target_id)
        print(f"   ↳ Merged tickets and incremented the counter. No new ticket created.")
    else:
        print(f"\n✅ [AGENT REASONING] The AI verified this is a brand new defect. Saving to database...")
        
        # --- FIXED DB INSERT LOGIC ---
        conn = sqlite3.connect("data/jalan-ready.db")
        cursor = conn.cursor()
        
        # Safety catch: Force the state to AWAITING_INFO if the AI hallucinates PENDING_WEATHER
        wf_state = result.get('workflow_state', 'NEW')
        if wf_state == "PENDING_WEATHER":
            wf_state = "AWAITING_INFO"
            
        # We now properly save latitude and longitude!
        cursor.execute("""
            INSERT INTO reports (
                latitude, longitude, road_name, defect_type, urgency_score, workflow_state, 
                jurisdiction, reasoning_path, timestamp, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            result.get('latitude', 0.0),
            result.get('longitude', 0.0),
            result.get('road_name', 'Unknown'),
            result.get('defect_type', 'Unknown'),
            result.get('urgency_score', 0),
            wf_state,
            result.get('assigned_authority', 'Unknown'),
            result.get('reasoning_path', '')
        ))
        
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"   ↳ Successfully created Active Report #{new_id} in the database!")

if __name__ == "__main__":
    run_demo()