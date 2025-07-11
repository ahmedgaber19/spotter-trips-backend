"""
API Views for route calculation and ELD generation
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging
from datetime import datetime

from utils.data_classes import TripRequest, RouteResponse
from utils.constants import ERROR_MESSAGES
from services.route_service import RouteService
from services.eld_service import ELDService
from services.hos_calculator import HOSCalculator

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class RouteCalculationView(APIView):
    """
    Main API endpoint for route calculation and ELD generation
    """
    
    def post(self, request):
        """
        Calculate route and generate ELD logs
        
        Expected input:
        {
            "current_location": "New York, NY",
            "pickup_location": "Philadelphia, PA",
            "dropoff_location": "Atlanta, GA", 
            "cycle_used": 45
        }
        """
        try:
            # Parse and validate input
            data = request.data
            
            # Validate required fields
            required_fields = ['current_location', 'pickup_location', 'dropoff_location', 'cycle_used']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {'error': f'Missing required field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create trip request object
            trip_request = TripRequest(
                current_location=data['current_location'],
                pickup_location=data['pickup_location'],
                dropoff_location=data['dropoff_location'],
                cycle_used=int(data['cycle_used'])
            )
            
            # Initialize services
            route_service = RouteService()
            eld_service = ELDService()
            hos_calculator = HOSCalculator()
            
            # Calculate route
            logger.info(f"Calculating route from {trip_request.current_location} to {trip_request.dropoff_location}")
            route_data = route_service.calculate_route(trip_request)
            
            # Generate ELD logs
            logger.info("Generating ELD logs")
            eld_logs = eld_service.generate_logs(route_data, trip_request)
            
            # Calculate HOS compliance
            logger.info("Calculating HOS compliance")
            hos_status = hos_calculator.calculate_compliance(trip_request, route_data)
            
            # Build response
            response_data = RouteResponse(
                route=route_data['route'],
                stops=route_data['stops'],
                fuel_stops=route_data['fuel_stops'],
                eld_logs=eld_logs,
                hos_status=hos_status
            )
            
            return Response(response_data.to_dict(), status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.error(f"Route calculation error: {str(e)}")
            return Response(
                {'error': 'Internal server error during route calculation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring and Vercel deployment
    """
    
    def get(self, request):
        """
        Return health status and basic info
        """
        try:
            return Response({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'service': 'Spotter Trucking API',
                'endpoints': {
                    'route_calculation': '/api/calculate-route/',
                    'health': '/api/health/'
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
