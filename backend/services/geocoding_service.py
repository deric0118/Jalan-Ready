import os
import googlemaps
from dotenv import load_dotenv

load_dotenv(override=True)

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

    def find_nearby_infrastructure(self, lat: float, lon: float, radius_meters: int = 150) -> dict:
        """
        Tool for the AI to scan for nearby critical infrastructure (schools, hospitals)
        to dynamically adjust the urgency score.
        """
        if not self.gmaps:
            return {"error": "Cannot search infrastructure without API key."}

        try:
            places_found = []
            
            # 1. Search for Schools
            school_res = self.gmaps.places_nearby(location=(lat, lon), radius=radius_meters, type='school')
            for place in school_res.get('results', []):
                places_found.append({"name": place.get('name'), "type": "School"})
                
            # 2. Search for Hospitals
            hospital_res = self.gmaps.places_nearby(location=(lat, lon), radius=radius_meters, type='hospital')
            for place in hospital_res.get('results', []):
                places_found.append({"name": place.get('name'), "type": "Hospital"})

            if places_found:
                return {"critical_infrastructure_nearby": True, "facilities": places_found}
            else:
                return {"critical_infrastructure_nearby": False, "facilities": []}

        except Exception as e:
            return {"error": str(e)}