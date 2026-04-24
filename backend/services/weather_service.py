import requests
from datetime import datetime, timedelta

class WeatherService:
    def __init__(self):
        # Open-Meteo APIs (Free, no keys required)
        self.forecast_url = "https://api.open-meteo.com/v1/forecast"
        self.historical_url = "https://archive-api.open-meteo.com/v1/archive"
        self.geocode_url = "https://geocoding-api.open-meteo.com/v1/search"

    def get_coords_from_name(self, location_name: str):
        """
        Backward-compatible geocoding helper used by the orchestrator.
        Returns (lat, lon) or (None, None) on failure.
        """
        if not location_name:
            return None, None

        try:
            params = {
                "name": location_name,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            response = requests.get(self.geocode_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if not results:
                return None, None

            first = results[0]
            return first.get("latitude"), first.get("longitude")
        except Exception:
            return None, None

    def get_weather(self, lat: float, lon: float) -> str:
        """
        Backward-compatible weather helper used by the orchestrator.
        Returns simple labels expected by current reasoning rules.
        """
        try:
            analysis = self.analyze_conditions(lat, lon)
            if analysis.get("delay_recommended"):
                return "Heavy Rain"
            return "Clear"
        except Exception:
            return "Clear"

    def analyze_conditions(self, lat: float, lon: float) -> dict:
        """
        Analyzes past and future weather to generate scheduling constraints.
        """
        today = datetime.today()
        three_days_ago = today - timedelta(days=3)

        # 1. Check Historical Weather (Past 72 hours)
        hist_params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": three_days_ago.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "hourly": "precipitation"
        }
        
        hist_response = requests.get(self.historical_url, params=hist_params)
        hist_data = hist_response.json()
        
        # Sum all precipitation over the last 3 days
        total_past_rain = sum(hist_data.get("hourly", {}).get("precipitation", []))
        
        # Logic: If rain > 20mm, the sub-base is wet
        sub_base_wet = total_past_rain > 20.0
        
        # 2. Check Forecast Weather (Next 24 hours)
        cast_params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "precipitation_probability",
            "forecast_days": 1
        }
        
        cast_response = requests.get(self.forecast_url, params=cast_params)
        cast_data = cast_response.json()
        
        # Get max rain probability for today
        max_rain_prob = max(cast_data.get("hourly", {}).get("precipitation_probability", [0]))
        
        # 3. Formulate Agent Constraints
        delay_recommended = False
        note = ""

        if sub_base_wet:
            delay_recommended = True
            note = f"Caution: Heavy rain ({total_past_rain}mm) in past 72h. Sub-base may be wet. Recommend 24h delay."
        elif max_rain_prob > 60:
            delay_recommended = True
            note = f"Caution: {max_rain_prob}% chance of rain today. Avoid scheduling outdoor patching."

        return {
            "sub_base_wet": sub_base_wet,
            "total_past_rain_mm": round(total_past_rain, 1),
            "rain_probability_percent": max_rain_prob,
            "delay_recommended": delay_recommended,
            "agent_note": note
        }

# --- Quick Local Test ---
if __name__ == "__main__":
    service = WeatherService()
    # Test coordinates for Petaling Jaya, Selangor
    print(service.analyze_conditions(22.707447, 9.382115))