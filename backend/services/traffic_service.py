import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

class TrafficService:
    def __init__(self):
        """
        Initializes the Traffic Service using the Google Maps Distance Matrix API.
        """
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        
        if not self.api_key:
            raise ValueError("⚠️ GOOGLE_MAPS_API_KEY not found in .env file. Please check your environment variables.")

    def analyze_traffic_constraints(self, origin: str, destination: str, scheduled_time: datetime = None) -> dict:
        """
        Analyzes real-time or future traffic density using Google Maps.
        Compares normal duration vs duration_in_traffic to give Agentic recommendations.
        
        :param origin: GPS coordinates or address of the contractor depot (e.g., "3.1073,101.6067")
        :param destination: GPS coordinates of the road defect
        :param scheduled_time: A datetime object for when the work is scheduled. Defaults to now.
        """
        if scheduled_time is None:
            scheduled_time = datetime.now()

        # Google Maps requires 'departure_time' to be a Unix timestamp to calculate traffic
        departure_timestamp = int(scheduled_time.timestamp())

        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": origin,
            "destinations": destination,
            "departure_time": departure_timestamp,
            "key": self.api_key,
            "traffic_model": "best_guess" # Options: best_guess, pessimistic, optimistic
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if data.get("status") != "OK":
                return self._fallback_error(f"Google API Error: {data.get('status')}")

            element = data["rows"][0]["elements"][0]
            if element.get("status") != "OK":
                return self._fallback_error("Route not found between origin and destination.")

            # Extract durations in seconds
            normal_duration_secs = element["duration"]["value"]
            # duration_in_traffic is only returned if departure_time is provided and the route is valid
            traffic_duration_secs = element.get("duration_in_traffic", {}).get("value", normal_duration_secs)

            # Calculate how much longer the trip takes due to traffic
            traffic_multiplier = traffic_duration_secs / normal_duration_secs

            return self._reason_traffic_impact(traffic_multiplier, normal_duration_secs, traffic_duration_secs)

        except Exception as e:
            return self._fallback_error(str(e))

    def _reason_traffic_impact(self, multiplier: float, normal_secs: int, traffic_secs: int) -> dict:
        """
        The Agentic Reasoning block. Translates raw API numbers into workflow decisions.
        """
        delay_recommended = False
        traffic_density = "Low"
        note = "Traffic conditions are optimal. Proceed with standard scheduling."

        # Agentic Rules based on real data
        if multiplier >= 1.5:  # Route takes 50% longer than normal
            delay_recommended = True
            traffic_density = "Severe"
            note = f"⚠️ Caution: Route currently takes {multiplier:.1f}x longer due to severe traffic ({(traffic_secs//60)} mins vs normal {(normal_secs//60)} mins). Recommend delaying dispatch to avoid gridlock."
        
        elif multiplier >= 1.2:  # Route takes 20% longer
            traffic_density = "High"
            note = f"Notice: High traffic density detected ({(traffic_secs//60)} mins). Standard repairs can proceed with caution."
            
        elif multiplier >= 1.05:
            traffic_density = "Moderate"
            note = "Notice: Traffic is moderate. Proceed with standard safety vehicles."

        return {
            "traffic_density": traffic_density,
            "normal_duration_mins": normal_secs // 60,
            "traffic_duration_mins": traffic_secs // 60,
            "delay_recommended": delay_recommended,
            "agent_note": note
        }

    def _fallback_error(self, error_msg: str) -> dict:
        """Graceful degradation if the API fails."""
        return {
            "traffic_density": "Unknown",
            "delay_recommended": False,
            "agent_note": f"⚠️ Traffic data unavailable ({error_msg}). Proceed with default scheduling."
        }

# --- Quick Local Test ---
if __name__ == "__main__":
    traffic = TrafficService()
    
    # Test 1: JKR Petaling to Sunway Pyramid (Use Lat/Lon strings or addresses)
    origin_depot = "3.1073,101.6067" 
    defect_location = "3.0730,101.6070"
    
    print("--- REAL GOOGLE MAPS TRAFFIC TEST ---")
    result = traffic.analyze_traffic_constraints(origin=origin_depot, destination=defect_location)
    
    import json
    print(json.dumps(result, indent=2))