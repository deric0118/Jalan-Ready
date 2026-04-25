import json
import os
from dotenv import load_dotenv

from zhipuai import ZhipuAI

# Explicit backend imports (using relative imports)
from ..services.vision_service import VisionService
from ..services.traffic_service import TrafficService
from ..services.weather_service import WeatherService
from ..services.geocoding_service import GeocodingService
from .database_manager import DatabaseManager
from .state_manager import StateManager 
from ..services.email_service import EmailService

# Import the engine tool for user communication
from .engine_tools import tool_c_user_communicator 

load_dotenv(override=True)

class JalanReadyAgent:
    def __init__(self):
        """
        Initializes the True Autonomous Orchestrator.
        Loads tools dynamically from backend/config/agent_tools.json
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
        self.geocoding_service = GeocodingService() 
        self.email_service = EmailService() 
        
        self.db = DatabaseManager()
        self.state_manager = StateManager(self.db)
        
        self.depot_location = "3.1073, 101.6067" # JKR Central Depot 
        self.current_image_path = None # Store image path for email attachment

        # 🚀 LOAD EXTERNAL CONFIGURATIONS (Separation of Concerns)
        self.config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
        tools_path = os.path.join(self.config_dir, "agent_tools.json")
        
        try:
            with open(tools_path, "r", encoding="utf-8") as file:
                self.tools = json.load(file)
            print("✅ [SYSTEM] Successfully loaded agent_tools.json")
        except Exception as e:
            print(f"⚠️ [SYSTEM ERROR] Could not load agent_tools.json. Did you create backend/config/agent_tools.json? Error: {e}")
            self.tools = []

    def process_new_report(self, image_path: str, location_input: str) -> dict:
        """
        The Entry Point. Loads prompt dynamically from backend/config/system_prompt.md
        """
        print(f"\n--- 🚀 Agent Activated: New Report at [{location_input}] ---")
        self.current_image_path = image_path 

        print("[SENSORY INPUT] Parsing dashcam image through YOLO...")
        vision_data = self.vision_service.analyze_image(image_path)
        self.current_vision_confidence = vision_data.get('confidence', 0.95) if isinstance(vision_data, dict) else 0.95
        
        prompt_path = os.path.join(self.config_dir, "system_prompt.md")
        try:
            with open(prompt_path, "r", encoding="utf-8") as file:
                system_prompt = file.read()
        except Exception as e:
            print(f"⚠️ [SYSTEM ERROR] Could not load system_prompt.md. Error: {e}")
            return {"error": "Prompt configuration missing."}
        
        user_message = f"Citizen report location input: '{location_input}'. Vision sensor detects: {json.dumps(vision_data)}. Please take over orchestration. Depot is at {self.depot_location}."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        return self._execute_agent_loop(messages)

    def plan_logistics_route(self, depot_gps: str, tasks: list) -> dict:
        """
        The Second Brain: Acts as a Logistics Dispatcher to sequence multi-stop routes.
        """
        if not self.glm_client:
            return {"error": "ZAI API Key missing.", "optimized_order": [t['id'] for t in tasks], "reasoning": "API Offline. Default order."}

        system_prompt = """
        You are the Chief Logistics AI for Jalan-Ready.
        Your job is to sequence a multi-stop repair route for a construction team.
        You will be provided with the starting Depot GPS, and a list of tasks with their GPS coordinates and urgency scores.
        
        Your Goal: Determine the most logical sequence to visit these locations, prioritizing clustered locations to minimize travel time, while also factoring in high urgency.
        
        Return ONLY a JSON object with this exact structure:
        {
          "optimized_order": [list of task IDs in the optimal sequence],
          "reasoning": "A brief explanation of why you chose this route (e.g., 'I routed you to task X first because it is closest to the depot, then grouped task Y and Z to avoid backtracking')."
        }
        """

        user_message = f"Depot Coordinates: {depot_gps}. Please sequence these tasks: {json.dumps(tasks)}"

        try:
            response = self.glm_client.chat.completions.create(
                model="ilmu-glm-5.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2
            )
            
            result_text = response.choices[0].message.content or ""
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            
            if json_match:
                return json.loads(json_match.group(0))
            else:
                return {"optimized_order": [t['id'] for t in tasks], "reasoning": "Failed to generate optimized route. Falling back to default order."}
                
        except Exception as e:
            return {"optimized_order": [t['id'] for t in tasks], "reasoning": f"AI Routing Error: {str(e)}"}

    def _execute_agent_loop(self, messages: list) -> dict:
        """The True Agentic Loop catching all tools."""
        if not self.glm_client:
            return {"error": "ZAI_API_KEY missing."}

        max_loops = 12 
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
                        
                        result = {}
                        
                        if function_name == "get_weather":
                            result = self.weather_service.analyze_conditions(arguments.get('latitude', 0), arguments.get('longitude', 0))
                        elif function_name == "get_traffic":
                            result = self.traffic_service.analyze_traffic_constraints(arguments.get('origin', ''), arguments.get('destination', ''))
                        elif function_name == "geocode_location":
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
                                result = self.db.check_historical_recurrence(arguments.get('latitude', 0), arguments.get('longitude', 0))
                            except AttributeError:
                                result = {"has_history": False, "note": "Mock DB Check: No recurrence found."}
                        elif function_name == "find_nearby_infrastructure":
                            try:
                                result = self.geocoding_service.find_nearby_infrastructure(arguments.get('latitude', 0), arguments.get('longitude', 0))
                            except Exception as e:
                                result = {"error": f"Infrastructure scan failed: {str(e)}"}
                        elif function_name == "send_user_prompt":
                            try:
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
                        elif function_name == "lookup_jurisdiction_contact":
                            try:
                                result = self.db.lookup_jurisdiction_contact(
                                    district=arguments.get('district', ''), 
                                    road_type=arguments.get('road_type', '')
                                )
                            except Exception as e:
                                result = {"error": f"Lookup failed: {str(e)}"}
                        elif function_name == "dispatch_work_order":
                            try:
                                email_data = {
                                    "yolo_label": arguments.get("defect_type", "Unknown"), 
                                    "road_name": arguments.get("road_name", "Unknown"),
                                    "confidence": self.current_vision_confidence,
                                    "weather": arguments.get("weather_state", "Clear"),
                                    "lat": arguments.get("latitude", 0.0),
                                    "lon": arguments.get("longitude", 0.0)
                                }
                                success = self.email_service.send_report(
                                    recipient_email=arguments.get("dispatch_email"),
                                    authority=arguments.get("assigned_authority"),
                                    urgency=arguments.get("urgency_score"),
                                    data=email_data,
                                    image_path=self.current_image_path
                                )
                                if success:
                                    result = {"status": "success", "message": f"Email sent to {arguments.get('dispatch_email')}"}
                                else:
                                    result = {"status": "failed", "message": "SMTP Email failed to send."}
                            except Exception as e:
                                result = {"error": f"Email dispatch error: {str(e)}"}
                        else:
                            result = {"error": "Unknown tool"}

                        print(f"✅ [TOOL DATA] {function_name} returned data.")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                    continue 

                else:
                    print("🤖 [AGENT THOUGHT] Orchestration complete. Generating final output.")
                    result_text = response_message.content or "" 
                    import re
                    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group(0))
                        except Exception as e:
                            return {"error": "Malformed JSON from Agent", "raw_ai_response": result_text}
                    else:
                        return {"error": "Agent failed to format JSON", "raw_ai_response": result_text}

            except Exception as e:
                print(f"⚠️ Z.AI Request Failed: {e}")
                return {"error": str(e)}
        
        return {"error": "Agent exceeded max tool-calling loops."}