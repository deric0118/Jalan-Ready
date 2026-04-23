# 🛣️ Jalan-Ready (NOT COMPLETED !!!)

> A smart infrastructure reporting system that combines YOLOv11 detection with Z.ai to seamlessly route validated pothole reports to the correct authorities (JKR/PBT).

## 📖 Overview
Jalan-Ready bridges the gap between the public and infrastructure authorities. By leveraging natural language processing and computer vision, this system allows citizens to report road defects conversationally. The backend utilizes Agentic AI workflows to automatically assess damage severity, calculate priority, check weather conditions, and route the report to the correct federal (JKR) or local (PBT) jurisdiction.

## 📸 Demo & Screenshots
*(Add a link to your YouTube demo/pitch video here)*

| User Chat Interface | Admin Dashboard |
| :---: | :---: |
| ![Chat UI Placeholder](https://via.placeholder.com/400x250?text=Chat+Interface+Screenshot) | ![Dashboard Placeholder](https://via.placeholder.com/400x250?text=Admin+Dashboard+Screenshot) |
| *Users report potholes conversationally* | *Officers view YOLOv11 analysis & priorities* |

## ✨ Key Features

### 👤 User-Facing (Public)
* **Chat-Based Reporting:** Users describe road issues in natural language and upload photos via a conversational interface.
* **Intelligent Information Gathering:** Z.ai/GLM asks targeted follow-up questions if location or critical details are missing.
* **Real-Time Damage Analysis:** Uploaded photos are instantly analyzed to identify the defect type and severity.
* **Priority Assessment Display:** Users receive an immediate priority assignment (Critical / High / Medium / Low) and an estimated response time.
* **Progress Tracking:** A dashboard to view the status of submitted reports (Submitted → Scheduled → In Progress → Completed).
* **Stateful Chat History:** Every conversation is saved, allowing users to return and seamlessly continue past interactions.

### 🧠 Backend & AI Agent
* **Multi-Modal Understanding:** Combines Z.ai text interpretation with YOLOv11 computer vision analysis.
* **Jurisdiction Auto-Routing:** Automatically determines if the road belongs to JKR (Federal) or a specific PBT (Local Council) based on geolocation.
* **Dynamic Priority Calculation:** Evaluates defect severity, road class, and traffic volume to compute an intelligent priority score.
* **Weather-Aware Scheduling:** Integrates weather forecasts to avoid scheduling asphalt repairs during rain.
* **Optimized Work Sequencing:** Suggests efficient travel routes for contractors to minimize disruption and travel time.
* **External Submission API:** Formats and dispatches reports to the correct authority via email or API.

### 🏢 Admin & Officer Dashboard
* **Centralized Dashboard:** JKR/PBT officers can view and manage all incoming reports within their jurisdiction.
* **Contractor Assignment:** View scheduled work orders and assign them to specific maintenance teams.
* **Manual Override & Status Updates:** Officers can adjust priorities, reassign jurisdictions, and update statuses to reflect in real-time on the public dashboard.

## 🛠️ Tech Stack
* **Computer Vision:** YOLOv11 (Road damage detection & severity assessment)
* **AI & LLM:** Z.ai / GLM (Conversational agent, multi-modal reasoning, priority calculation)
* **Language:** Python 
* **[Add your Frontend framework here, e.g., React, HTML/CSS]**
* **[Add your Database here, e.g., PostgreSQL, Firebase]**

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [[https://github.com/yourusername/Jalan-Ready.git](https://github.com/yourusername/Jalan-Ready.git)](https://github.com/deric0118/Jalan-Ready.git)
   cd Jalan-Ready
2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
5. **Environment Variables:**
   Create a .env file in the root directory and add your API keys:
   ```bash
   Z_AI_API_KEY=your_api_key_here
   MAPS_API_KEY=your_maps_api_key
6. **Run the application:**

