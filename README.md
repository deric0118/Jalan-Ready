# 🛣️ Jalan-Ready

> A smart infrastructure reporting system that combines YOLOv8 detection with Z.ai to seamlessly route validated pothole reports to the correct authorities (JKR/PBT).

## Project Documentation
[Pitching Video](https://drive.google.com/drive/u/0/folders/182utHFD4SaSKKhOpj3jFbU7usVUgBFJT)
Comprehensive technical documentation is provided in the `docs/` directory:

* **[Product Requirement Documentation (PRD)](./docs/Product_Requirement_Documentation.pdf)**: Detailed problem statement, user stories, and feature scope.
* **[System Analysis Documentation (SAD)](./docs/System_Analysis_Documentation.pdf)**: Technical architecture, data flow diagrams, and agentic workflow design.
* **[Quality Assurance Testing Documentation (QATD)](./docs/Quality_Assurance_Testing_Documentation.pdf)**: Test strategy, CI/CD thresholds, and edge-case validation results.

## 📖 Overview
Jalan-Ready bridges the gap between the public and infrastructure authorities. By leveraging natural language processing and computer vision, this system allows citizens to report road defects conversationally. The backend utilizes Agentic AI workflows to automatically assess damage severity, calculate priority, check weather conditions, and route the report to the correct federal (JKR) or local (PBT) jurisdiction in Selangor.

## ✨ Key Features

### 👤 User-Facing (Public)
* **AI-Powered Reporting:** Users upload photos of road damage; the system uses YOLOv8 for instant visual verification.
* **Automated Metadata Gathering:** Extracts location and additional notes to build a comprehensive context packet.
* **Real-Time Progress Tracking:** A 4-step live stepper (Report Received → AI Analysis → Repair In Progress → Completed) that updates automatically as contractors work.
* **Authenticated Access:** Secure login and signup system to track user contributions and report history.

### 🧠 Backend & AI Agent (Z.ai Orchestrator)
* **Multi-Modal Understanding:** Combines Z.ai (GLM-4/5) text interpretation with YOLOv8 computer vision analysis.
* **Jurisdiction Auto-Routing:** Automatically determines the correct authority (e.g., MBPJ, JKR) based on geolocation and road types.
* **Dynamic Priority & Reasoning:** Evaluates severity and context to assign urgency scores (Critical/High/Low) with full AI reasoning paths.
* **Automated Dispatch:** Instantly sends detailed email work orders to the assigned authority upon report validation.
* **Logistics Optimization:** Features an AI routing engine to sequence multiple repair stops for maintenance crews.

### 🏢 Contractor & Admin Portal
* **Real-Time Work Queue:** View "Unrepaired" lists specifically filtered by jurisdiction.
* **Status Management:** Contractors can mark reports as "In Progress" or "Resolved," which syncs instantly to the citizen's view.
* **Automatic Notification:** Authorities receive automated emails containing defect type, confidence scores, and weather conditions.

## 🛠️ Tech Stack
* **AI Engine:** Z.ai / GLM-5.1 (Agentic Orchestration, Routing, & Reasoning)
* **Computer Vision:** YOLOv8 (ONNX Runtime for local inference)
* **Backend:** FastAPI (Python)
* **Frontend:** HTML5, Tailwind CSS, JavaScript (ES6+)
* **Database:** SQLite3 (Relational storage for users and reports)
* **Background Processing:** Python-based Cron Engine for automated re-evaluations

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/deric0118/Jalan-Ready.git](https://github.com/deric0118/Jalan-Ready.git)
   cd Jalan-Ready
2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
4. **🧠 AI Model Setup**
   The system uses a YOLOv8 model exported to ONNX format for real-time defect detection.
   ```bash
   1. Download the `yolov8.onnx` file from our [Latest Release](https://github.com/deric0118/Jalan-Ready/releases/tag/v1.0.0)
   2. Create a folder named `models` in the root directory.
   3. Place `yolov8.onnx` inside the `models/` folder.
      - Required Path: `models/yolov8.onnx`
5. **Environment Variables:**
   Create a .env file in the root directory and add your API keys:
   ```bash
   # Z.AI GLM
   ZAI_API_KEY=your_zai_api_key
   AI_BASE_URL=[https://api.ilmu.ai/v4](https://api.ilmu.ai/v4)  # Or your specific endpoint
   # Google Maps (for Geocoding and Traffic)
   GOOGLE_MAPS_API_KEY=your_google_map_api_key

   # Email (SMTP)
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=sender_email_address
   SMTP_PASSWORD=app_password (16 characters without spacing)

   #OpenWeatherMap (for Weather Data)
   OPENWEATHER_API_KEY=your_open_weather_api_key
6. **Run the application:**
   You must run three separate terminals to host the full system:
   ```bash
   Terminal 1 (UserBackend API): python -m uvicorn backend.app:app --reload --port 8000
   Terminal 2 (ContractorBackend API): python -m uvicorn backend.contractor_app:app --port 8001 --reload
   Terminal 3 (Frontend Server): python -m http.server 8080

   Login page link: http://127.0.0.1:8080/login.html
   


