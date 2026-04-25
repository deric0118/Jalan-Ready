import sqlite3
import csv
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the orchestrator to access the Logistics AI Brain
from backend.core.orchestrator import JalanReadyAgent

app = FastAPI(title="Jalan-Ready Contractor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the AI for routing
routing_agent = JalanReadyAgent()

JALAN_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "jalan-ready.db")
)
CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "selangor_jurisdiction.csv")
)

def _get_jalan_conn():
    conn = sqlite3.connect(JALAN_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/contractor/authorities")
def get_authorities():
    authorities = set()
    try:
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('authority'):
                    authorities.add(row['authority'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read CSV: {e}")
    return {"authorities": sorted(list(authorities))}

@app.get("/api/contractor/tasks")
def get_contractor_tasks(authority: str):
    conn = _get_jalan_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM reports
        WHERE jurisdiction = ? AND workflow_state NOT IN ('RESOLVED', 'REJECTED')
        ORDER BY urgency_score DESC
    """, (authority,))
    unrepaired = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT * FROM reports
        WHERE jurisdiction = ? AND workflow_state = 'RESOLVED'
        ORDER BY updated_at DESC
    """, (authority,))
    repaired = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return {"unrepaired": unrepaired, "repaired": repaired}

# NEW: Model accepts a LIST of task IDs
class MultiTaskActionRequest(BaseModel):
    task_ids: list[int]
    authority: str

@app.post("/api/contractor/tasks/generate")
def generate_multi_route(payload: MultiTaskActionRequest):
    if not payload.task_ids:
        raise HTTPException(status_code=400, detail="No tasks selected.")

    conn = _get_jalan_conn()
    cursor = conn.cursor()
    
    # Update states to IN_PROGRESS
    placeholders = ','.join('?' for _ in payload.task_ids)
    cursor.execute(
        f"UPDATE reports SET workflow_state = 'IN_PROGRESS', updated_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders}) AND jurisdiction = ?",
        (*payload.task_ids, payload.authority)
    )
    conn.commit()

    # Fetch task details for the AI
    cursor.execute(f"SELECT id, latitude, longitude, urgency_score, defect_type FROM reports WHERE id IN ({placeholders})", payload.task_ids)
    tasks_data = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Get Depot GPS
    depot_lat, depot_lon = "3.1073", "101.6067" 
    try:
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['authority'] == payload.authority:
                    depot_lat = row['depot_lat']
                    depot_lon = row['depot_lon']
                    break
    except Exception:
        pass

    depot_gps = f"{depot_lat},{depot_lon}"

    # Call the AI to sequence them
    ai_route_plan = routing_agent.plan_logistics_route(depot_gps, tasks_data)
    
    optimized_ids = ai_route_plan.get("optimized_order", payload.task_ids)
    reasoning = ai_route_plan.get("reasoning", "Standard routing applied.")

    # Build the multi-stop Google Maps URL
    maps_url = f"https://www.google.com/maps/dir/{depot_gps}"
    
    for opt_id in optimized_ids:
        # Find the coordinates for this specific ID
        task = next((t for t in tasks_data if t['id'] == opt_id), None)
        if task:
            maps_url += f"/{task['latitude']},{task['longitude']}"

    return {
        "status": "success", 
        "maps_url": maps_url, 
        "reasoning": reasoning,
        "optimized_sequence": optimized_ids
    }

@app.post("/api/contractor/tasks/resolve")
def resolve_multi_tasks(payload: MultiTaskActionRequest):
    if not payload.task_ids:
        raise HTTPException(status_code=400, detail="No tasks selected.")

    conn = _get_jalan_conn()
    cursor = conn.cursor()
    
    placeholders = ','.join('?' for _ in payload.task_ids)
    cursor.execute(
        f"UPDATE reports SET workflow_state = 'RESOLVED', updated_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders}) AND jurisdiction = ?",
        (*payload.task_ids, payload.authority)
    )
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": f"{len(payload.task_ids)} tasks marked as RESOLVED."}