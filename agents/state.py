# agents/state.py
from typing import TypedDict, List, Optional, Any
from langgraph.graph import MessagesState

class WorkflowState(MessagesState):
    # ---- Report identification ----
    report_id: Optional[str]           # e.g., "RPT-20260424-0001"
    user_id: Optional[int]

    # ---- User input ----
    raw_text: Optional[str]            # original user message
    image_path: Optional[str]          # path to uploaded image (local)
    # Extracted entities
    location_query: Optional[str]      # user quoted location
    coordinates: Optional[dict]        # {"lat": ..., "lng": ...}
    location_address: Optional[str]    # full address
    road_name: Optional[str]
    road_type: Optional[str]           # Federal, State, Municipal
    jurisdiction: Optional[str]        # "JKR Petaling", "MBPJ", etc.
    council_email: Optional[str]

    # ---- Data completeness ----
    missing_fields: List[str]          # fields GLM determines are missing

    # ---- Vision analysis ----
    defect_type: Optional[str]         # e.g., "pothole", "crack"
    severity: Optional[str]            # "Critical", "High", "Medium", "Low"
    vision_raw: Optional[dict]         # raw output from vision model

    # ---- Damage assessment ----
    priority_score: Optional[int]
    assessment_notes: Optional[str]
    recurring_flag: Optional[bool]     # True if recurring problem detected
    recurring_note: Optional[str]

    # ---- Scheduling ----
    weather_forecast: Optional[dict]   # forecast data from Open‑Meteo
    past_rain: Optional[dict]          # historical rain data
    traffic_data: Optional[dict]       # from Google Maps
    scheduled_time: Optional[str]      # ISO datetime string
    scheduling_notes: Optional[str]    # e.g., "delayed due to wet sub‑base"

    # ---- Dispatch ----
    work_order: Optional[dict]         # final formatted work order
    email_sent: Optional[bool]         # confirmation flag