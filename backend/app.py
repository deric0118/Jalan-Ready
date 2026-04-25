import base64
import hashlib
import hmac
import os
import secrets
import sqlite3
import tempfile
import shutil
import uuid  # <-- Added missing import
from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File, Form
from pydantic import BaseModel
from fastapi import BackgroundTasks

# Lazy load the orchestrator - only needed for report analysis, not for auth
try:
    from .core.orchestrator import JalanReadyAgent
    HAS_ORCHESTRATOR = True
except Exception as e:
    print(f"Warning: Could not load orchestrator: {e}")
    HAS_ORCHESTRATOR = False
    JalanReadyAgent = None

app = FastAPI()

# Allow your HTML/JS frontend to talk to this Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In a real app, put your frontend URL here
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize your Agent (only if available)
agent = JalanReadyAgent() if HAS_ORCHESTRATOR else None

USER_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "user_data.db")
)


def _get_user_conn():
    conn = sqlite3.connect(USER_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_user_db():
    conn = _get_user_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            phone_number TEXT NOT NULL UNIQUE,
            id_number TEXT NOT NULL UNIQUE,
            address TEXT NOT NULL,
            postcode TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    digest_b64 = base64.b64encode(digest).decode("utf-8")
    return f"{salt_b64}${digest_b64}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_b64, digest_b64 = stored_hash.split("$", 1)
        salt = base64.b64decode(salt_b64.encode("utf-8"))
        stored_digest = base64.b64decode(digest_b64.encode("utf-8"))
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
        return hmac.compare_digest(candidate, stored_digest)
    except Exception:
        return False


_init_user_db()

# Define what the incoming "Context Packet" should look like
class ReportData(BaseModel):
    yolo_label: str
    confidence: float
    gps_coordinates: str
    weather: str


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    phone_number: str
    id_number: str
    address: str
    postcode: str


class LoginRequest(BaseModel):
    email: str
    password: str

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


@app.post("/api/signup")
def signup(payload: SignupRequest):
    conn = _get_user_conn()
    cursor = conn.cursor()
    email = payload.email.strip().lower()
    phone_number = payload.phone_number.strip()
    id_number = payload.id_number.strip().upper()
    try:
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, phone_number, id_number, address, postcode)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.name.strip(),
                email,
                _hash_password(payload.password),
                phone_number,
                id_number,
                payload.address.strip(),
                payload.postcode.strip(),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail="Account already exists with this email, phone number, or ID number.",
        )

    cursor.execute(
        "SELECT id, name, email, phone_number, id_number, address, postcode FROM users WHERE email = ?",
        (email,),
    )
    user = cursor.fetchone()
    conn.close()

    return {
        "message": "Signup successful",
        "token": secrets.token_urlsafe(32),
        "user": dict(user),
    }


@app.post("/api/login")
def login(payload: LoginRequest):
    conn = _get_user_conn()
    cursor = conn.cursor()
    email = payload.email.strip().lower()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not _verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {
        "message": "Login successful",
        "token": secrets.token_urlsafe(32),
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone_number": user["phone_number"],
            "id_number": user["id_number"],
            "address": user["address"],
            "postcode": user["postcode"],
        },
    }


@app.post("/api/analyze")
async def analyze_report(
    image: UploadFile = File(...),
    location: str = Form(""),
    note: str = Form(""),
    lat: float = Form(None),
    lon: float = Form(None),
):
    if not agent:
        raise HTTPException(status_code=503, detail="Backend orchestrator not available.")

    temp_dir = None
    try:
        # Save uploaded image
        temp_dir = tempfile.mkdtemp(prefix="jalan_ready_")
        image_path = Path(temp_dir) / image.filename
        with open(image_path, "wb") as f:
            content = await image.read()
            f.write(content)

        # Build location string
        location_input = location if location else "Unknown location"
        if note:
            location_input += f" ({note})"

        result = agent.process_new_report(str(image_path), location_input)

        if "error" in result:
            detail = result["error"]
            status_code = 503 if "Z.ai" in detail or "API key" in detail or "authentication failed" in detail.lower() else 500
            raise HTTPException(status_code=status_code, detail=detail)

        # Extract fields (adjust keys based on your orchestrator's actual output)
        work_order_id = result.get("work_order_id", str(uuid.uuid4()))
        defect_type = result.get("defect_type", "Pothole")
        confidence = result.get("confidence", 0.95)
        priority = result.get("priority", "P2")
        authority = result.get("assigned_authority", "MBPJ")
        reasoning = result.get("reasoning", "")
        location_desc = result.get("location_description", location_input)
        urgency_score = result.get("urgency_score", 50)  # Default 50 if not provided
        lat_val = lat if lat is not None else result.get("latitude", 0.0)
        lon_val = lon if lon is not None else result.get("longitude", 0.0)

        # Store using DatabaseManager
        agent.db.create_work_order(
            id=work_order_id,
            defect_type=defect_type,
            priority=priority,
            authority=authority,
            confidence=confidence,
            reasoning=reasoning,
            location=location_desc,
            lat=lat_val,
            lon=lon_val,
            image_path=str(image_path),
            status="NEW"   # or "pending_approval"
        )

        # Return frontend-compatible response
        return {
            "success": True,
            "work_order": {
                "id": work_order_id,
                "urgency_score": urgency_score,
                "detections": [{"class": defect_type, "confidence": confidence}],
                "decision": {
                    "assigned_to": authority,
                    "priority": priority,
                    "reasoning": reasoning,
                    "sla_hours": result.get("sla_hours", 48)
                }
            }
        }

    except Exception as e:
        print(f"[ERROR] /api/analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

@app.post("/api/dispatch")
async def dispatch_work_order(payload: dict, background_tasks: BackgroundTasks):
    wo_id = payload.get("work_order_id")
    if not wo_id:
        raise HTTPException(status_code=400, detail="Missing work_order_id")

    wo = agent.db.get_work_order(wo_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")

    # Allow only if status is 'NEW' or 'pending_approval'
    if wo["workflow_state"] not in ["NEW", "pending_approval"]:
        return {"success": False, "message": f"Work order already {wo['workflow_state']}"}

    # Prepare email data
    email_data = {
        "yolo_label": wo["defect_type"],
        "road_name": wo["road_name"],
        "confidence": wo["confidence"],
        "weather": "Clear",   # optionally fetch live weather
        "lat": wo["latitude"],
        "lon": wo["longitude"]
    }

    # Get jurisdiction contact using your existing method
    # Note: you may need to pass district/road_type – 
    # for now, derive from location or set default
    jurisdiction = agent.db.lookup_jurisdiction_contact(
        district="Petaling",   # example; you can extract from wo["road_name"]
        road_type="primary"
    )
    recipient = jurisdiction.get("safe_dispatch_email", "default@example.com")
    authority_name = jurisdiction.get("authority", wo["jurisdiction"])

    # Send email in background
    background_tasks.add_task(
        agent.email_service.send_report,
        recipient_email=recipient,
        authority=authority_name,
        urgency=wo["urgency_score"],
        data=email_data,
        image_path=wo["image_path"]
    )

    # Update status
    agent.db.update_work_order_status(wo_id, "REPORTED")   # or "DISPATCHED"

    return {"success": True, "message": f"Work order dispatched to {authority_name}"}

# Run this file using: uvicorn app:app --reload