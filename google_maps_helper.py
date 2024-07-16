import googlemaps
from datetime import datetime, timedelta
from typing import Union, Tuple

# Please ensure you have set your API key
API_KEY = 'Replace with your actual API key'
gmaps = googlemaps.Client(key=API_KEY)

def calculate_travel_details(start_location: str, end_location: str, departure_time: Union[datetime, None] = None, arrival_time: Union[datetime, None] = None, mode: str = "transit") -> Tuple[float, float, datetime, datetime]:
    """
    Calculate travel details between two locations using Google Maps API.

    Args:
        start_location (str): The starting location.
        end_location (str): The destination location.
        departure_time (Union[datetime, None], optional): The departure time. Defaults to None.
        arrival_time (Union[datetime, None], optional): The arrival time. Defaults to None.
        mode (str, optional): The mode of transport (e.g., "transit", "driving"). Defaults to "transit".

    Returns:
        Tuple[float, float, datetime, datetime]: The distance in kilometers, duration in minutes, departure time, and arrival time.
    """
    directions_result = None
    if departure_time:
        directions_result = gmaps.directions(start_location, end_location, mode=mode, departure_time=departure_time)
    elif arrival_time:
        directions_result = gmaps.directions(start_location, end_location, mode=mode, arrival_time=arrival_time)
    else: 
        directions_result = gmaps.directions(start_location, end_location, mode=mode)

    if directions_result:
        leg = directions_result[0]['legs'][0]
        distance = leg['distance']['value'] / 1000  # Distance in kilometers
        duration = leg['duration']['value'] / 60  # Duration in minutes
        
        if departure_time:
            arrival_time = departure_time + timedelta(minutes=duration)
            return distance, duration, departure_time, arrival_time
        elif arrival_time:
            departure_time = arrival_time - timedelta(minutes=duration)
            return distance, duration, departure_time, arrival_time
        else:
            return distance, duration, None, None
    
    return float('inf'), float('inf'), None, None
