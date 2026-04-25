import json
import os
from dotenv import load_dotenv

from zhipuai import ZhipuAI

# Explicit backend imports
from backend.services.vision_service import VisionService
from backend.services.traffic_service import TrafficService
from backend.services.weather_service import WeatherService
from backend.services.geocoding_service import GeocodingService # <-- NEW
from backend.core.database_manager import DatabaseManager
from backend.core.state_manager import StateManager 

# Import the engine tool for user communication
from backend.core.engine_tools import tool_c_user_communicator # <-- NEW

load_dotenv(override=True)

class JalanReadyAgent:
    def __init__(self):
        """
        Initializes the True Autonomous Orchestrator with 7 Tool Integrations.
        """
        api_key = os.getenv("ZAI_API_KEY")
        base_url = os.getenv("ZAI_BASE_URL")
        
        # Connect to Proxy for Z.ai
        if api_key:
            if base_url:
                self.glm_client = ZhipuAI(api_key=api_key, base_url=base_url)
            else:
                self.glm_client = ZhipuAI(api_key=api_key)
        else:
            self.glm_client = None
            
        self.vision_service = VisionService(model_weight_path="models/yolov8.onnx")
        self.traffic_service = TrafficService()
        self.weather_service = WeatherService()
        self.geocoding_service = GeocodingService() # Added Geocoding Service
        
        self.db = DatabaseManager()
        self.state_manager = StateManager(self.db)
        
        self.depot_location = "3.1073, 101.6067" # JKR Central Depot 

        # 🚀 REGISTERING ALL 7 TOOLS FOR THE AI BRAIN
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "check_nearby_reports",
                    "description": "Searches the database for active reports within 50 meters.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"}
                        },
                        "required": ["latitude", "longitude"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Returns current conditions and rain forecast for a GPS coordinate.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"}
                        },
                        "required": ["latitude", "longitude"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_traffic",
                    "description": "Returns travel time and congestion level from depot to defect.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "origin": {"type": "string", "description": "Depot GPS"},
                            "destination": {"type": "string", "description": "Defect GPS"}
                        },
                        "required": ["origin", "destination"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "geocode_location",
                    "description": "Converts a user-provided address or place name into GPS coordinates.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location_name": {"type": "string", "description": "Address or landmark name"}
                        },
                        "required": ["location_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "reverse_geocode",
                    "description": "Takes GPS coordinates and returns the full address, road name, and road classification.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"}
                        },
                        "required": ["latitude", "longitude"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_historical_failure",
                    "description": "Checks database for previous reports within 100m. Returns true if repeat failure.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"}
                        },
                        "required": ["latitude", "longitude"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_nearby_infrastructure",
                    "description": "Scans for nearby schools or hospitals within 150m to dynamically adjust urgency.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"}
                        },
                        "required": ["latitude", "longitude"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_user_prompt",
                    "description": "Sends a message to the user asking for missing info (e.g., exact location).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "The exact message to send to the user"}
                        },
                        "required": ["message"]
                    }
                }
            }
        ]

    def process_new_report(self, image_path: str, location_input: str) -> dict:
        """
        The Entry Point. Note that 'location_input' might be raw text now, not just GPS.
        """
        print(f"\n--- 🚀 Agent Activated: New Report at [{location_input}] ---")

        # Step 1: The "Eyes"
        print("[SENSORY INPUT] Parsing dashcam image through YOLO...")
        vision_data = self.vision_service.analyze_image(image_path)
        
        # Step 2: System Instructions (Your updated prompt with Infrastructure & RCA)
        system_prompt = """
        You are the Central Reasoning Engine for Jalan-Ready, a fully autonomous road-defect management system for Selangor, Malaysia.

        Your job is to orchestrate the entire lifecycle of a new report: triage, assessment, scheduling, and dispatch preparation.
        You have a set of tools that provide live data and execute actions. You MUST use them proactively before making any final decision. Do not assume - always call the tools to gather real information.

        ## Reasoning Rules - You Must Follow These

        ### 1. Data Completeness Check
        Before proceeding, confirm that you have GPS coordinates and a defect type. If GPS is missing and no address can be extracted, call `send_user_prompt` to ask for the location. Do NOT continue until coordinates are resolved.

        ### 2. Deduplication Check (Agentic Reasoning)
        - Call `check_nearby_reports` using the GPS coordinates. 
        - Look at the returned data. If there is an active report with a similar `defect_type` at the same `road_name`, you must conclude this is a duplicate report by another citizen.
        - If it IS a duplicate, set "is_duplicate" to true, and put the matching ID in "duplicate_of_id".

        ### 3. Jurisdiction Assignment (CRITICAL MALAYSIAN HIERARCHY)
        CRITICAL RULE: Google Maps reverse geocoding often incorrectly snaps highway coordinates to nearby municipal side roads. You MUST check BOTH the user's original location input and the `reverse_geocode` output.
        If EITHER the user input OR the geocode output contains 'Federal', 'Highway', 'Lebuhraya', 'Expressway', 'E', or 'FT', you MUST ignore the side road and assign authority based on the highway:
        - Expressways ('E', 'Lebuhraya', 'Expressway') -> Assign to 'Highway Concessionaire (LLM)'.
        - Federal Roads ('FT', 'Federal', 'Highway') -> Assign to 'JKR Federal'.
        - State Roads (Starts with 'B' and not 'FT') -> Assign to 'JKR State'.
        - Municipal Roads (Standard 'Jalan' without above prefixes) -> Map the locality to the exact Local Council (e.g., 'MBPJ', 'MBSA', 'MPK').

        ### 4. Urgency Calculation (Base + Modifiers)
        - 'sinkhole', 'structural_failure' -> 90
        - 'pothole', 'alligator_cracking' -> 60
        - 'crack' -> 40
        - 'faded_markings' -> 20

        Modifiers:
        - Historical recurrence (`check_historical_failure`): If the tool returns a history of failures here, apply +30 urgency. You MUST conduct Root Cause Analysis (RCA) in your reasoning path (e.g., deduce why the previous patch failed). Add "Structural Audit Required" to the workflow state or reasoning.
        - Critical Infrastructure (`find_nearby_infrastructure`): If a school or hospital is nearby, apply +20 urgency to protect vulnerable pedestrians and emergency routes.
        - Weather influence (`get_weather`): Heavy rain + sinkhole = 100. Rain + surface work = 'AWAITING_INFO'.
        - Traffic impact (`get_traffic`): High congestion + major arterial = +10 urgency.

        ### 5. Scheduling Recommendation
        - If wet conditions prevent work, set workflow_state to 'AWAITING_INFO'. The system's background engine will automatically re-trigger you in 24 hours to re-evaluate the weather.
        - IMPORTANT: `scheduled_time` must NEVER be null. If delayed by weather, output "24 Hours from now (Pending Re-evaluation)". Otherwise, propose a specific off-peak time window for immediate dispatch.

        ### 6. Final Output Format
        After gathering all tool data, output ONLY a JSON object:
        {
          "is_duplicate": <boolean>,
          "duplicate_of_id": "<ID or null>",
          "latitude": <float>,
          "longitude": <float>,
          "urgency_score": <int>,
          "assigned_authority": "<exact authority name>",
          "workflow_state": "<NEW | AWAITING_INFO | REPORTED | IN_PROGRESS | ESCALATED | RESOLVED | MANUAL_REVIEW>",
          "road_name": "<extracted road name>",
          "defect_type": "<from vision>",
          "scheduled_time": "<String, e.g., 'Tomorrow Morning' or '24 Hours from now'>",
          "reasoning_path": "<concise sentence explaining the decision>",
          "dispatch_email": "<destination email or placeholder>"
        }
        """
        
        # Step 3: Trigger the Agent
        user_message = f"Citizen report location input: '{location_input}'. Vision sensor detects: {json.dumps(vision_data)}. Please take over orchestration. Depot is at {self.depot_location}."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        return self._execute_agent_loop(messages)

    def _execute_agent_loop(self, messages: list) -> dict:
        """
        The True Agentic Loop catching all 7 tools.
        """
        if not self.glm_client:
            return {"error": "ZAI_API_KEY missing."}

        max_loops = 8 # Increased limit since it might need to call 4+ tools in a row
        loop_count = 0

        while loop_count < max_loops:
            loop_count += 1
            try:
                response = self.glm_client.chat.completions.create(
                    model="ilmu-glm-5.1",
                    messages=messages,
                    tools=self.tools,
                    temperature=0.1
                )
                
                response_message = response.choices[0].message
                messages.append(response_message.model_dump(exclude_none=True)) 

                if response_message.tool_calls:
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        
                        print(f"🤖 [AGENT THOUGHT] Using tool: {function_name}()")
                        
                        # --- TOOL EXECUTION ROUTER ---
                        result = {}
                        
                        if function_name == "get_weather":
                            result = self.weather_service.analyze_conditions(arguments.get('latitude', 0), arguments.get('longitude', 0))
                            
                        elif function_name == "get_traffic":
                            result = self.traffic_service.analyze_traffic_constraints(arguments.get('origin', ''), arguments.get('destination', ''))
                            
                        elif function_name == "geocode_location":
                            # Use your geocoding service (add a fallback if it fails)
                            try:
                                result = self.geocoding_service.geocode(arguments.get('location_name', ''))
                            except Exception as e:
                                result = {"error": f"Failed to geocode: {str(e)}"}
                                
                        elif function_name == "reverse_geocode":
                            try:
                                result = self.geocoding_service.reverse_geocode(arguments.get('latitude', 0), arguments.get('longitude', 0))
                            except Exception as e:
                                result = {"error": "Reverse geocode failed", "road_prefix": "Unknown"}
                                
                        elif function_name == "check_historical_failure":
                            try:
                                # Now returns a detailed dictionary to enable RCA reasoning
                                result = self.db.check_historical_recurrence(arguments.get('latitude', 0), arguments.get('longitude', 0))
                            except AttributeError:
                                # Safe hackathon fallback if method isn't fully coded yet
                                result = {"has_history": False, "note": "Mock DB Check: No recurrence found."}
                                
                        elif function_name == "find_nearby_infrastructure":
                            try:
                                # Triggers the new Google Maps Places search for schools/hospitals
                                result = self.geocoding_service.find_nearby_infrastructure(arguments.get('latitude', 0), arguments.get('longitude', 0))
                            except Exception as e:
                                result = {"error": f"Infrastructure scan failed: {str(e)}"}
                                
                        elif function_name == "send_user_prompt":
                            try:
                                # Calls the user communicator tool
                                result = tool_c_user_communicator(message=arguments.get('message', ''))
                            except Exception:
                                result = {"status": "success", "action": "Prompted user", "content": arguments.get('message')}
                        
                        elif function_name == "check_nearby_reports":
                            try:
                                result = self.db.get_nearby_active_reports(arguments.get('latitude', 0), arguments.get('longitude', 0))
                                if not result:
                                    result = {"message": "No nearby active reports found."}
                            except AttributeError:
                                result = {"message": "Database error checking reports."}
                                
                        else:
                            result = {"error": "Unknown tool"}

                        print(f"✅ [TOOL DATA] {function_name} returned data.")
                        
                        # Feed the result back to Z.ai
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                        
                    continue # Restart loop to let AI process the new tool data

                else:
                    print("🤖 [AGENT THOUGHT] Orchestration complete. Generating final output.")
                    # Safely grab the text, defaulting to empty string if None
                    result_text = response_message.content or "" 
                    
                    # 🚀 ROBUST JSON EXTRACTION
                    import re
                    # Hunt for anything that looks like { ... }
                    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                    
                    if json_match:
                        try:
                            # Parse only the matched JSON part
                            return json.loads(json_match.group(0))
                        except Exception as e:
                            print(f"⚠️ [JSON PARSE ERROR] Python couldn't read the JSON: {e}")
                            # Fallback: show exactly what the AI said so we can debug
                            return {"error": "Malformed JSON from Agent", "raw_ai_response": result_text}
                    else:
                        print("⚠️ [NO JSON FOUND] Agent replied with plain text instead of JSON.")
                        return {"error": "Agent failed to format JSON", "raw_ai_response": result_text}

            except Exception as e:
                print(f"⚠️ Z.AI Request Failed: {e}")
                return {"error": str(e)}
        
        return {"error": "Agent exceeded max tool-calling loops."}

# --- TEST BLOCK ---
if __name__ == "__main__":
    orchestrator = JalanReadyAgent()
    # Testing with raw text to see if the agent uses 'geocode_location' first!
    final_decision = orchestrator.process_new_report(
        image_path="C:\\Users\\njxnj\\Downloads\\Telegram Desktop\\test_road.jpg",
        location_input="Jalan SS2/24, Petaling Jaya" 
    )
    print("\n--- 🧠 FINAL JSON ---")
    print(json.dumps(final_decision, indent=2))