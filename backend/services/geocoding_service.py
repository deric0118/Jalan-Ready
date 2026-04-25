import os
import googlemaps
from dotenv import load_dotenv

load_dotenv()

class GeocodingService:
    def __init__(self):
        """Initializes the Geocoding Service using Google Maps."""
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if self.api_key:
            self.gmaps = googlemaps.Client(key=self.api_key)
        else:
            self.gmaps = None
            print("⚠️ GOOGLE_MAPS_API_KEY missing. Geocoding will run in MOCK mode.")

    def geocode(self, location_name: str) -> dict:
        """Converts a text address into GPS coordinates."""
        if not self.gmaps:
            return {"latitude": 3.1012, "longitude": 101.6530, "note": "MOCK COORDS"}

        try:
            result = self.gmaps.geocode(location_name)
            if result:
                loc = result[0]['geometry']['location']
                return {"latitude": loc['lat'], "longitude": loc['lng']}
            return {"error": "Location not found"}
        except Exception as e:
            return {"error": str(e)}

    def reverse_geocode(self, lat: float, lon: float) -> dict:
        """Converts GPS coordinates into a human-readable street address."""
        if not self.gmaps:
            return {"address": "Jalan SS7/2, Petaling Jaya (MOCK)", "road_prefix": "Municipal"}

        try:
            result = self.gmaps.reverse_geocode((lat, lon))
            if result:
                address = result[0]['formatted_address']
                # Try to grab the specific route name
                route = next((comp['long_name'] for comp in result[0]['address_components'] if 'route' in comp['types']), address)
                return {"address": address, "road_name": route}
            return {"error": "Address not found"}
        except Exception as e:
            return {"error": str(e)}