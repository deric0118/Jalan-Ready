import math

def calculate_distance(lat1, lon1, lat2, lon2):
    try:
        # Force float conversion to prevent TypeErrors during math ops
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    except (ValueError, TypeError):
        return 999.0 # Fail-safe: Return a large distance if coordinates are invalid

def tool_b_route_optimizer(tasks, start_lat, start_lon):
    """
    Tool B: Autonomous Route Optimizer (Greedy TSP).
    Inputs: 
        - tasks: List of sqlite3.Row or dict objects from the database.
        - start_lat/lon: The District HQ coordinates for the specific authority.
    Output: 
        - Optimized list of task dictionaries.
    """
    if not tasks:
        return []

    # Convert DB tuples to manageable dicts
    unvisited = []
    for t in tasks:
        unvisited.append({
            "id": t[0], "lat": t[2], "lon": t[3], 
            "road": t[4], "issue": t[5], "urgency": t[7]
        })

    optimized_route = []
    curr_lat, curr_lon = start_lat, start_lon

    while unvisited:
        # Strategy: Pick the next closest task that has a high urgency score
        # This is 'Reasoned Routing'
        next_task = min(unvisited, key=lambda x: (calculate_distance(curr_lat, curr_lon, x['lat'], x['lon']) / (x['urgency']/100)))
        
        optimized_route.append(next_task)
        curr_lat, curr_lon = next_task['lat'], next_task['lon']
        unvisited.remove(next_task)

    return optimized_route

def tool_c_user_communicator(report_id="TEMP_ID", message_type="", message=""):
    """
    Tool C: User Communicator. 
    The AI uses this to ask the citizen for missing details (like a better address).
    """
    print(f"📡 [COMM-LINK] AI Message to Citizen: '{message}'")
    return {"status": "Message sent to user UI", "message_content": message}