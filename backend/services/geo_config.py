SELANGOR_DISTRICTS = {
    "JKR Gombak": {"lat": 3.243, "lon": 101.703, "locations": ["Batu Arang", 
                                                               "Batu Caves", 
                                                               "Kuang", 
                                                               "Rawang"], 
                   "email": "petalingjkr.hackathon@gmail.com"},
    "JKR Hulu Langat": {"lat": 2.993, "lon": 101.789, "locations": ["Ampang", 
                                                                    "Bangi", 
                                                                    "Cheras", 
                                                                    "Kajang", 
                                                                    "Semenyih"], 
                   "email": "petalingjkr.hackathon@gmail.com"},
    
    "JKR Hulu Selangor": {"lat": 3.564, "lon": 101.652, "locations": ["Batang Kali", 
                                                                      "Kuala Kubu Baru", 
                                                                      "Rasa", 
                                                                      "Serendah"], 
                   "email": "petalingjkr.hackathon@gmail.com"},
    
    "JKR Klang": {"lat": 3.047, "lon": 101.449, "locations": ["Kapar", 
                                                              "Klang", 
                                                              "Pulau Indah", 
                                                              "Port Klang"], 
                   "email": "petalingjkr.hackathon@gmail.com"},
    
    "JKR Kuala Langat": {"lat": 2.812, "lon": 101.503, "locations": ["Banting", 
                                                                     "Jenjarom", 
                                                                     "Tanjong Sepat", 
                                                                     "Telok Panglima Garang"], 
                   "email": "petalingjkr.hackathon@gmail.com"},
    
    "JKR Kuala Selangor": {"lat": 3.341, "lon": 101.250, "locations": ["Bestari Jaya", 
                                                                       "Jeram", 
                                                                       "Kuala Selangor", 
                                                                       "Tanjong Karang"], 
                   "email": "petalingjkr.hackathon@gmail.com"},
    
    "JKR Petaling": {"lat": 3.073, "lon": 101.518, "locations": ["PJ", 
                                                                 "Puchong", 
                                                                 "Shah Alam", 
                                                                 "Subang Jaya", 
                                                                 "Sungai Buloh"], 
                   "email": "petalingjkr.hackathon@gmail.com"},
    
    "JKR Sabak Bernam": {"lat": 3.763, "lon": 101.008, "locations": ["Sabak Bernam", 
                                                                     "Sekinchan", 
                                                                     "Sungai Besar"], 
                   "email": "petalingjkr.hackathon@gmail.com"},
    
    "JKR Sepang": {"lat": 2.817, "lon": 101.751, "locations": ["Cyberjaya", 
                                                               "Dengkil", 
                                                               "KLIA", 
                                                               "Sepang"], 
                   "email": "petalingjkr.hackathon@gmail.com"},
}

def determine_jurisdiction(address: str) -> str:
    """
    Scans the human-readable address for matching district keywords.
    """
    if not address:
        return "UNKNOWN - Requires Manual Triage"

    address_lower = address.lower()
    
    # Updated to use your SELANGOR_DISTRICTS dictionary
    for authority, data in SELANGOR_DISTRICTS.items():
        for location in data["locations"]:
            if location.lower() in address_lower:
                return authority
                
    # Fallback if no specific JKR district matches
    return "Local Council / Municipal"

def get_authority_email(jurisdiction: str) -> str:
    """Retrieves the email address for a given authority."""
    if jurisdiction in SELANGOR_DISTRICTS:
        return SELANGOR_DISTRICTS[jurisdiction]["email"]
    return "petalingjkr.hackathon@gmail.com"

def get_authority_hq(jurisdiction: str):
    """Returns (lat, lon) for the District Office HQ."""
    if jurisdiction in SELANGOR_DISTRICTS:
        return SELANGOR_DISTRICTS[jurisdiction]["lat"], SELANGOR_DISTRICTS[jurisdiction]["lon"]
    
    # Fallback to a central Selangor location if unknown
    return 3.073, 101.518