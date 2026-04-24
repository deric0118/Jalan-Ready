# agents/workflow.py
import logging
from typing import Optional

from langgraph.graph import StateGraph, END

from agents.state import WorkflowState

logger = logging.getLogger(__name__)


# ── Node 1: Input Processing ────────────────────────────────
def input_processing_node(state: WorkflowState) -> dict:
    """
    Placeholder: Extract location/description from raw_text,
    geocode, check completeness. In real implementation, calls GLM.
    """
    logger.info("--- Input Processing Node ---")
    # For skeleton, we pretend data is complete → no missing fields.
    # Later GLM will determine missing_fields and set coordinates etc.
    return {
        "missing_fields": [],
        # simulated extraction (real will be filled by GLM)
        "coordinates": {"lat": 3.15658, "lng": 101.70469},
        "location_address": "Jalan Ampang, Kuala Lumpur",
        "road_type": "Federal",
    }


# ── Node 2: Damage Assessment ───────────────────────────────
def damage_assessment_node(state: WorkflowState) -> dict:
    """
    Placeholder: Run vision model, check recurring issues,
    compute priority using GLM reasoning about severity, road class, etc.
    """
    logger.info("--- Damage Assessment Node ---")
    # Simulated output
    return {
        "defect_type": "pothole",
        "severity": "High",
        "priority_score": 85,
        "recurring_flag": False,
        "recurring_note": "",
    }


# ── Node 3: Scheduling ──────────────────────────────────────
def scheduling_node(state: WorkflowState) -> dict:
    """
    Placeholder: Fetch weather+traffic, decide time window,
    apply past-rain logic to detect wet sub‑base.
    """
    logger.info("--- Scheduling Node ---")
    # Simulated – real node will integrate Open‑Meteo & Google Maps
    return {
        "scheduled_time": "2026-04-25T10:00:00",
        "scheduling_notes": "No rain today; sub‑base dry.",
    }


# ── Node 4: Dispatch ────────────────────────────────────────
def dispatch_node(state: WorkflowState) -> dict:
    """
    Placeholder: Determine jurisdiction (JKR/PBT), format work order,
    send email via email_service.
    """
    logger.info("--- Dispatch Node ---")
    # Simulated
    return {
        "jurisdiction": "JKR Petaling",
        "council_email": "aduan.petaling@jkr.gov.my",
        "work_order": {
            "summary": "Pothole on Jalan Ampang",
            "priority": "High",
            "scheduled": "2026-04-25T10:00:00",
        },
        "email_sent": True,
    }


# ── Conditional routing ─────────────────────────────────────
def should_continue(state: WorkflowState) -> str:
    """
    After input processing, decide: if data incomplete → wait for user.
    Otherwise → continue to damage assessment.
    """
    missing = state.get("missing_fields", [])
    if missing:
        logger.info(f"Missing fields: {missing}. Pausing workflow.")
        return "end"  # Wait for user input
    else:
        return "damage_assessment"


# ── Build the graph ─────────────────────────────────────────
def build_workflow() -> StateGraph:
    # Create graph with our state type
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("input_processing", input_processing_node)
    workflow.add_node("damage_assessment", damage_assessment_node)
    workflow.add_node("scheduling", scheduling_node)
    workflow.add_node("dispatch", dispatch_node)

    # Edges
    workflow.set_entry_point("input_processing")
    workflow.add_conditional_edges(
        "input_processing",
        should_continue,
        {
            "damage_assessment": "damage_assessment",
            "end": END,          # pause until user supplies missing info
        },
    )
    workflow.add_edge("damage_assessment", "scheduling")
    workflow.add_edge("scheduling", "dispatch")
    workflow.add_edge("dispatch", END)

    return workflow.compile()

# ═══════════════════════════════════════════════════════════════
# Temporary test harness — runs only when executing THIS file
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uuid
    logging.basicConfig(level=logging.INFO)

    graph = build_workflow()
    initial_state = {
        "raw_text": "Large pothole near KLCC",
        "image_path": "test_road.jpg",
        "messages": [],          # MessagesState requires this
    }
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = graph.invoke(initial_state, config)

    print("\n✅ Skeleton test passed. Final state:")
    for k, v in result.items():
        if k != "messages":
            print(f"  {k}: {v}")