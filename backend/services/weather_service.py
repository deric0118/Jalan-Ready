import requests
import os
from dotenv import load_dotenv
load_dotenv() # This loads the variables from .env into your environment

class WeatherService:
    def __init__(self, api_key=None):
        # Prefer API key from environment variables for security
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        # New Geocoding URL for location name resolution
        self.geo_url = "http://api.openweathermap.org/geo/1.0/direct"

    def get_weather(self, lat=None, lon=None, location_name=None):
        """
        Fetches real-time weather. 
        Returns: 'Raining', 'Cloudy', 'Clear', or 'Unknown'
        """
        if not self.api_key:
            print("⚠️ [WEATHER] No API Key found. Defaulting to 'Clear' for demo.")
            return "Clear"

        if (lat is None or lon is None) and location_name:
            try:
                geo_params = {"q": f"{location_name}, Selangor, MY", "limit": 1, "appid": self.api_key}
                geo_resp = requests.get(self.geo_url, params=geo_params, timeout=5)
                geo_resp.raise_for_status()
                geo_data = geo_resp.json()
                
                if geo_data:
                    lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
                    print(f"📍 [GEO] Resolved '{location_name}' to {lat}, {lon}")
                else:
                    print(f"⚠️ [GEO] Could not resolve name: {location_name}")
                    return "Unknown"
            except Exception as e:
                print(f"⚠️ [GEO ERROR] Resolution failed: {e}")
                return "Unknown"

        # Final guard: if we still don't have coordinates after name check
        if lat is None or lon is None:
            return "Unknown"
    
        try:
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric"
            }
            response = requests.get(self.base_url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            weather_main = data["weather"][0]["main"]
            
            # Map API codes to our internal Logic
            if weather_main in ["Rain", "Drizzle", "Thunderstorm"]:
                return "Raining"
            return weather_main

        except Exception as e:
            print(f"⚠️ [WEATHER ERROR] Fetch failed: {e}. Falling back to 'Clear'.")
            return "Clear"
        
    def get_coords_from_name(self, location_name):
        """
        Standalone method to resolve a name to GPS coordinates.
        Refactored to support both Selangor and Kuala Lumpur regions.
        """
        if not self.api_key:
            return None, None

        # List of target regions to ensure local precision
        regions = ["Selangor", "Kuala Lumpur"]
        
        try:
            for region in regions:
                # Try searching in each region sequentially
                geo_params = {
                    "q": f"{location_name}, {region}, MY", 
                    "limit": 1, 
                    "appid": self.api_key
                }
                response = requests.get(self.geo_url, params=geo_params, timeout=3)
                response.raise_for_status()
                data = response.json()

                if data:
                    lat, lon = data[0]["lat"], data[0]["lon"]
                    # Validation: Ensure the result is actually within our target bounds
                    # (Approx bounds for Selangor/KL: Lat 2.5-3.8, Lon 100.8-102.0)
                    if 2.5 <= lat <= 3.8 and 100.8 <= lon <= 102.0:
                        return lat, lon
            
            # If loop finishes with no valid data
            print(f"⚠️ [GEO] '{location_name}' not found in Selangor or KL.")
            return None, None
            
        except Exception as e:
            print(f"⚠️ [GEO ERROR] Failed to resolve '{location_name}': {e}")
            return None, None