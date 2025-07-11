"""
Helper utility functions
"""
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import re
import math


def parse_address(address: str) -> str:
    """Clean and standardize address format"""
    # Remove extra whitespace and standardize
    address = re.sub(r'\s+', ' ', address.strip())
    return address


def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculate distance between two coordinates using Haversine formula
    Returns distance in miles
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in miles
    r = 3959
    
    return c * r


def format_duration(hours: float) -> str:
    """Format duration in hours to human-readable format"""
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes} minutes"
    elif hours < 24:
        hours_int = int(hours)
        minutes = int((hours - hours_int) * 60)
        if minutes == 0:
            return f"{hours_int} hours"
        return f"{hours_int} hours {minutes} minutes"
    else:
        days = int(hours // 24)
        remaining_hours = int(hours % 24)
        return f"{days} days {remaining_hours} hours"


def calculate_fuel_stops(route_distance: float, start_mile: float = 0) -> List[float]:
    """
    Calculate fuel stop positions along route
    Returns list of mile markers where fuel stops should occur
    """
    fuel_stops = []
    current_mile = start_mile
    
    while current_mile < route_distance:
        current_mile += 1000  # Every 1000 miles
        if current_mile < route_distance:
            fuel_stops.append(current_mile)
    
    return fuel_stops


def interpolate_route_position(coordinates: List[List[float]], mile_marker: float, 
                             total_distance: float) -> List[float]:
    """
    Find approximate coordinates at a specific mile marker along the route
    """
    if not coordinates or mile_marker <= 0:
        return coordinates[0] if coordinates else [0, 0]
    
    if mile_marker >= total_distance:
        return coordinates[-1] if coordinates else [0, 0]
    
    # Simple linear interpolation (could be more sophisticated)
    position_ratio = mile_marker / total_distance
    index = int(position_ratio * (len(coordinates) - 1))
    
    if index >= len(coordinates):
        return coordinates[-1]
    
    return coordinates[index]


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate that coordinates are within valid ranges"""
    return -90 <= lat <= 90 and -180 <= lon <= 180


def time_to_next_hour(dt: datetime) -> datetime:
    """Round datetime to next hour"""
    return dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def calculate_arrival_time(start_time: datetime, duration_hours: float) -> datetime:
    """Calculate arrival time given start time and duration"""
    return start_time + timedelta(hours=duration_hours)


def is_within_driving_hours(current_time: datetime, start_time: datetime, 
                           max_hours: float = 11) -> bool:
    """Check if current time is within allowed driving hours from start"""
    elapsed = (current_time - start_time).total_seconds() / 3600
    return elapsed <= max_hours


def format_coordinates(coordinates: List[List[float]]) -> List[List[float]]:
    """Format coordinates to ensure proper precision"""
    return [[round(coord[0], 6), round(coord[1], 6)] for coord in coordinates]


def chunk_coordinates(coordinates: List[List[float]], max_points: int = 100) -> List[List[float]]:
    """Reduce coordinate density for frontend performance"""
    if len(coordinates) <= max_points:
        return coordinates
    
    step = len(coordinates) // max_points
    return coordinates[::step]
