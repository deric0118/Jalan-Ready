import base64
import hashlib
import hmac
import os
import secrets
import sqlite3
import tempfile
import shutil
from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File, Form
from pydantic import BaseModel

WORK_ORDER_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "work_orders.db")
)

def _init_work_order_db():
    conn = sqlite3.connect(WORK_ORDER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            id TEXT PRIMARY KEY,
            defect_type TEXT,
            priority TEXT,
            authority TEXT,
            confidence REAL,
            reasoning TEXT,
            location TEXT,
            lat REAL,
            lon REAL,
            image_path TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

_init_work_order_db()

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
    """
    Receives a road damage image and metadata, processes it through the orchestrator,
    and returns analysis results including priority, assigned authority, and work order details.
    """
    if not agent:
        raise HTTPException(
            status_code=503,
            detail="Backend orchestrator not available. Check server logs."
        )
    
    temp_dir = None
    try:
        # Create temporary directory to store the image
        temp_dir = tempfile.mkdtemp(prefix="jalan_ready_")
        image_path = Path(temp_dir) / image.filename
        
        # Save the uploaded image to temporary location
        with open(image_path, "wb") as f:
            content = await image.read()
            f.write(content)
        
        # Build location string
        location_input = location if location else "Unknown location"
        if note:
            location_input += f" ({note})"
        
        print(f"[API] Image saved to {image_path}")
        print(f"[API] Processing report: location={location_input}, lat={lat}, lon={lon}")
        
        # Call the orchestrator to analyze the image
        result = agent.process_new_report(str(image_path), location_input)
        
        # Return the result in the expected format
        return {
            "success": True,
            "work_order": result
        }
    
    except Exception as e:
        print(f"[ERROR] Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
    
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


# Run this file using: uvicorn app:app --reload