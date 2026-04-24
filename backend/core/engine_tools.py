import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine formula to calculate distance between two GPS points in km."""
    R = 6371 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def tool_b_route_optimizer(tasks, start_lat=3.118, start_lon=101.677):
    """
    Tool B: Autonomous Route Optimizer.
    Input: List of tuples from the database.
    Output: Optimized list of dicts.
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

def tool_c_user_communicator(report_id, message_type):
    print(f"📡 [COMM-LINK] Report ID {report_id}: Action required -> {message_type}")
    return True