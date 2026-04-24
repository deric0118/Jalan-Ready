import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env
load_dotenv(override=True)

env_path = Path(".env")
print(f"Reading .env from: {env_path.resolve()}")
print(f"File exists: {env_path.exists()}")
if env_path.exists():
    print("First 3 lines of .env:")
    with env_path.open() as f:
        for i, line in enumerate(f):
            if i >= 3:
                break
            # mask long values
            if "=" in line:
                key = line.split("=")[0]
                print(f"  {key}= ... (masked)")
            else:
                print(f"  {line.strip()}")

print("=== .env values (masked) ===")
for var in ["ZAI_API_KEY", "SMTP_USERNAME", "SMTP_PASSWORD"]:
    val = os.getenv(var)
    if val:
        # Show first 4 chars only, for security
        print(f"{var}: {val[:4]}{'*' * (len(val)-4)} (length {len(val)})")
    else:
        print(f"{var}: NOT FOUND")
print("===========================\n")

print("=" * 60)
print("🔧 Jalan-Ready API Connection Tests")
print("=" * 60)

# ── 1. Z.AI GLM (via ILMU API) ──────────────────────────
def test_glm():
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        print("❌ LLM: ZAI_API_KEY not found in .env")
        return

    url = "https://api.ilmu.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": "ilmu-glm-5.1",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": 'Reply with exactly: "OK"'},
        ],
        "max_tokens": 10,
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            reply = r.json()["choices"][0]["message"]["content"]
            print(f"✅ LLM (ILMU): Connected — reply: {reply}")
        else:
            print(f"❌ LLM (ILMU): HTTP {r.status_code} — {r.text[:200]}")
    except Exception as e:
        print(f"❌ LLM (ILMU): {e}")


# ── 2. Google Maps Geocoding ─────────────────────────────
def test_google_maps():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("❌ Google Maps: GOOGLE_MAPS_API_KEY not found in .env")
        return

    address = "Jalan Ampang, Kuala Lumpur"
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}

    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200 and r.json().get("status") == "OK":
            loc = r.json()["results"][0]["geometry"]["location"]
            print(
                f"✅ Google Maps: '{address}' → "
                f"lat={loc['lat']:.5f}, lng={loc['lng']:.5f}"
            )
        else:
            print(f"❌ Google Maps: status={r.json().get('status')} — {r.text[:200]}")
    except Exception as e:
        print(f"❌ Google Maps: {e}")


# ── 3. Open-Meteo Weather ────────────────────────────────
def test_openmeteo():
    lat, lon = 3.1390, 101.6869  # Kuala Lumpur

    print("→ Testing Open-Meteo Forecast…")
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,precipitation_probability",
            "timezone": "Asia/Kuala_Lumpur",
            "forecast_days": 1,
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(
                "✅ Open-Meteo Forecast: "
                f"elevation={data.get('elevation', 'N/A')} m, "
                f"timezone={data.get('timezone', 'N/A')}"
            )
        else:
            print(f"❌ Open-Meteo Forecast: HTTP {r.status_code}")
    except Exception as e:
        print(f"❌ Open-Meteo Forecast: {e}")

    print("→ Testing Open-Meteo Historical…")
    try:
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": "2026-04-20",
            "end_date": "2026-04-20",
            "hourly": "precipitation",
            "timezone": "Asia/Kuala_Lumpur",
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            print("✅ Open-Meteo Historical: Connected (rain data available)")
        else:
            print(f"❌ Open-Meteo Historical: HTTP {r.status_code}")
    except Exception as e:
        print(f"❌ Open-Meteo Historical: {e}")


# ── 4. SMTP Email ────────────────────────────────────────
def test_email():
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    receiver = os.getenv("SMTP_USERNAME")  # send to yourself for the test

    if not username or not password:
        print("❌ SMTP Email: SMTP_USERNAME / SMTP_PASSWORD not set in .env")
        return

    msg = MIMEMultipart()
    msg["From"] = username
    msg["To"] = receiver
    msg["Subject"] = "Jalan-Ready — SMTP Test"
    body = "This is a test email from Jalan-Ready setup. If you see this, SMTP is configured correctly."
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(username, password)
        server.sendmail(username, receiver, msg.as_string())
        server.quit()
        print(f"✅ SMTP Email: Test email sent to {receiver}")
    except smtplib.SMTPAuthenticationError:
        print(
            "❌ SMTP Email: Authentication failed. "
            "If using Gmail, make sure you created an App Password "
            "(not your regular password)."
        )
    except Exception as e:
        print(f"❌ SMTP Email: {e}")


# ── Run all tests ────────────────────────────────────────
print()
test_glm()
print()
test_google_maps()
print()
test_openmeteo()
print()
test_email()
print()
print("=" * 60)
print("🏁 All tests completed.")