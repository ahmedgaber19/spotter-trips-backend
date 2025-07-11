"""
Route calculation service using OpenRouteService API
"""
import requests
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta

from django.conf import settings
from utils.data_classes import TripRequest, Location, Stop, RouteData
from utils.constants import OPENROUTESERVICE_API_KEY, ROUTE_CONSTANTS, API_URLS, ERROR_MESSAGES
from utils.helpers import calculate_distance, calculate_fuel_stops, interpolate_route_position

logger = logging.getLogger(__name__)


class RouteService:
    """
    Service for route calculation and planning
    """
    
    def __init__(self):
        self.base_url = API_URLS['OPENROUTE_BASE']
        self.nominatim_url = API_URLS['NOMINATIM_BASE']
        
    def calculate_route(self, trip_request: TripRequest) -> Dict[str, Any]:
        """
        Main route calculation method
        
        Returns:
        {
            'route': RouteData,
            'stops': List[Stop],
            'fuel_stops': List[Stop]
        }
        """
        try:
            # Step 1: Geocode all locations
            current_loc = self.geocode_location(trip_request.current_location)
            pickup_loc = self.geocode_location(trip_request.pickup_location)
            dropoff_loc = self.geocode_location(trip_request.dropoff_location)
            # Step 2: Calculate multi-stop route
            route_data = self._calculate_multi_stop_route([current_loc, pickup_loc, dropoff_loc])
            
            # Step 3: Calculate stops (rest breaks)
            stops = self._calculate_rest_stops(route_data, trip_request)
            
            # Step 4: Calculate fuel stops
            fuel_stops = self._calculate_fuel_stops(route_data)
            
            return {
                'route': route_data,
                'stops': stops,
                'fuel_stops': fuel_stops
            }
            
        except Exception as e:
            logger.error(f"Route calculation failed: {str(e)}")
            raise Exception(f"Route calculation failed: {str(e)}")
    
    def geocode_location(self, address: str) -> Location:
        """
        Convert address to coordinates using Nominatim (OpenStreetMap)
        """
        try:
            params = {
                'q': address,
                'format': 'json',
                'limit': 1
            }
            
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                headers={'User-Agent': 'spotter-service-backend'}
            )
            
            if response.status_code != 200:
                raise Exception(f"Geocoding API error: {response.status_code}")
            
            data = response.json()
            
            if not data:
                raise Exception(f"Location not found: {address}")
            
            result = data[0]
            return Location(
                address=result.get('display_name', address),
                latitude=float(result['lat']),
                longitude=float(result['lon'])
            )
            
        except Exception as e:
            logger.error(f"Geocoding failed for {address}: {str(e)}")
            raise Exception(f"Could not geocode location: {address}")
    
    def _calculate_multi_stop_route(self, locations: List[Location]) -> RouteData:
        """
        Calculate route through multiple locations using OpenRouteService API
        """
        try:
            # Prepare coordinates in [lon, lat] format
            print('hello')
            coordinates = [[loc.longitude, loc.latitude] for loc in locations]
            print('hello2')
            print('Coordinates for route:', coordinates)

            # Call OpenRouteService API
            api_response = self._call_openroute_api(coordinates)


  
   
            route = api_response['routes'][0]
            distance = route['summary']['distance'] / 1609.34  # meters to miles
            duration = route['summary']['duration'] / 3600      # seconds to hours
            
            # OpenRouteService returns geometry as an encoded polyline string, not coordinates
            # For now, we'll use the input waypoints as the route coordinates
            # In production, you might want to decode the polyline for more detailed path
            coordinates = [[loc.longitude, loc.latitude] for loc in locations]
            
            print('Route parsed successfully')

            return RouteData(
                distance=distance,
                duration=duration,
                coordinates=coordinates
            )

        except Exception as e:
            logger.error(f"Route calculation failed: {str(e)}")
            raise Exception("Could not calculate route")
    
    def _calculate_rest_stops(self, route_data: RouteData, trip_request: TripRequest) -> List[Stop]:
        """
        Calculate mandatory rest stops based on HOS rules
        """
        stops = []
        current_time = datetime.now()
        distance_traveled = 0
        driving_time = 0
        
        # Add pickup stop
        pickup_coords = route_data.coordinates[1] if len(route_data.coordinates) > 1 else route_data.coordinates[0]
        stops.append(Stop(
            type='pickup',
            location=Location(
                address='Pickup Location',
                latitude=pickup_coords[1],
                longitude=pickup_coords[0]
            ),
            time=current_time + timedelta(hours=driving_time),
            duration=ROUTE_CONSTANTS['PICKUP_DURATION'],
            description='Pickup cargo'
        ))
        
        current_time += timedelta(hours=ROUTE_CONSTANTS['PICKUP_DURATION'])
        
        # Calculate rest stops every 11 hours of driving
        remaining_distance = route_data.distance
        
        while remaining_distance > 0:
            # Drive for up to 11 hours
            max_drive_distance = ROUTE_CONSTANTS['AVERAGE_SPEED'] * 11
            drive_distance = min(max_drive_distance, remaining_distance)
            drive_time = drive_distance / ROUTE_CONSTANTS['AVERAGE_SPEED']
            
            distance_traveled += drive_distance
            driving_time += drive_time
            current_time += timedelta(hours=drive_time)
            
            # If we haven't reached the destination, add rest stop
            if distance_traveled < route_data.distance:
                rest_coords = interpolate_route_position(
                    route_data.coordinates,
                    distance_traveled,
                    route_data.distance
                )
                
                stops.append(Stop(
                    type='rest',
                    location=Location(
                        address='Rest Area',
                        latitude=rest_coords[1],
                        longitude=rest_coords[0]
                    ),
                    time=current_time,
                    duration=10.0,  # 10-hour mandatory rest
                    description='Mandatory 10-hour rest period'
                ))
                
                current_time += timedelta(hours=10)
            
            remaining_distance -= drive_distance
        
        # Add dropoff stop
        dropoff_coords = route_data.coordinates[-1] if route_data.coordinates else [0, 0]
        stops.append(Stop(
            type='dropoff',
            location=Location(
                address='Dropoff Location',
                latitude=dropoff_coords[1],
                longitude=dropoff_coords[0]
            ),
            time=current_time,
            duration=ROUTE_CONSTANTS['DROPOFF_DURATION'],
            description='Deliver cargo'
        ))
        
        return stops
    
    def _calculate_fuel_stops(self, route_data: RouteData) -> List[Stop]:
        """
        Calculate fuel stops every 1000 miles
        """
        fuel_stops = []
        fuel_mile_markers = calculate_fuel_stops(route_data.distance)
        
        for mile_marker in fuel_mile_markers:
            coords = interpolate_route_position(
                route_data.coordinates,
                mile_marker,
                route_data.distance
            )
            
            fuel_stops.append(Stop(
                type='fuel',
                location=Location(
                    address='Fuel Stop',
                    latitude=coords[1],
                    longitude=coords[0]
                ),
                time=datetime.now(),  # Will be calculated properly in ELD service
                duration=ROUTE_CONSTANTS['FUEL_STOP_DURATION'],
                description=f'Fuel stop at mile {mile_marker:.0f}'
            ))
        
        return fuel_stops
    
    def _call_openroute_api(self, coordinates: List[List[float]]) -> Dict[str, Any]:
        """
        Call OpenRouteService API (when API key is available)
        """
        try:
            headers = {
                'Authorization': OPENROUTESERVICE_API_KEY,
                'Content-Type': 'application/json'
            }
            
            data = {
                'coordinates': coordinates,
            }
            print('Calling OpenRouteService API with data:', data)
            
            response = requests.post(
                f"{self.base_url}/directions/driving-car",
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"InternalServerError: {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            json_response = response.json()
            return json_response
            
        except Exception as e:
            logger.error(f"OpenRoute API call failed: {str(e)}")
            raise Exception("Route service unavailable")
