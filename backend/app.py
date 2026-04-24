# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.orchestrator import JalanReadyAgent # Import your Brain!

app = FastAPI()

# Allow your HTML/JS frontend to talk to this Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In a real app, put your frontend URL here
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize your Agent
agent = JalanReadyAgent()

# Define what the incoming "Context Packet" should look like
class ReportData(BaseModel):
    yolo_label: str
    confidence: float
    gps_coordinates: str
    weather: str

# The Waiter receiving the order!
@app.post("/submit_report")
def submit_report(data: ReportData):
    # 1. Convert the incoming JS data into a Python dictionary
    context_packet = data.dict()
    
    # 2. Give it to the Kitchen (Your Orchestrator)
    result = agent.process_new_report(context_packet)
    
    # 3. Bring the food back to the Customer (Return to JS)
    return {
        "status": "success",
        "agent_response": result
    }

# Run this file using: uvicorn app:app --reload