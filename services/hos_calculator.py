"""
Hours of Service (HOS) calculator for compliance checking
"""
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta, date

from utils.data_classes import TripRequest, RouteData, HOSStatus, DailyLog
from utils.constants import HOS_LIMITS, ERROR_MESSAGES

logger = logging.getLogger(__name__)


class HOSCalculator:
    """
    Service for calculating Hours of Service compliance
    """
    
    def calculate_compliance(self, trip_request: TripRequest, route_data: Dict[str, Any]) -> HOSStatus:
        """
        Calculate HOS compliance status for the trip
        
        Returns HOSStatus with compliance information
        """
        try:
            route = route_data['route']
            
            # Calculate basic HOS metrics
            remaining_hours = HOS_LIMITS['WEEKLY_LIMIT'] - trip_request.cycle_used
            
            # Estimate drive time for today (simplified)
            estimated_drive_time = min(route.duration, HOS_LIMITS['DAILY_DRIVE_LIMIT'])
            
            # Calculate estimated duty time (drive time + stops)
            estimated_duty_time = self._calculate_estimated_duty_time(route_data)
            
            # Calculate next reset time (simplified - assume 8-day cycle)
            next_reset = datetime.now() + timedelta(days=HOS_LIMITS['CYCLE_DAYS'])
            
            # Check for violations
            violations = self._check_violations(
                trip_request, route, estimated_drive_time, estimated_duty_time
            )
            
            return HOSStatus(
                cycle_used=trip_request.cycle_used,
                remaining_hours=remaining_hours,
                drive_time_today=estimated_drive_time,
                duty_time_today=estimated_duty_time,
                next_reset=next_reset,
                violations=violations
            )
            
        except Exception as e:
            logger.error(f"HOS calculation failed: {str(e)}")
            raise Exception(f"Could not calculate HOS compliance: {str(e)}")
    
    def _calculate_estimated_duty_time(self, route_data: Dict[str, Any]) -> float:
        """
        Calculate estimated total duty time for the trip
        """
        route = route_data['route']
        stops = route_data['stops']
        
        # Start with driving time
        total_duty_time = route.duration
        
        # Add time for stops that count as on-duty
        for stop in stops:
            if stop.type in ['pickup', 'dropoff', 'fuel']:
                total_duty_time += stop.duration
        
        # Cap at daily limit
        return min(total_duty_time, HOS_LIMITS['DAILY_DUTY_LIMIT'])
    
    def _check_violations(self, trip_request: TripRequest, route: RouteData, 
                         drive_time: float, duty_time: float) -> List[str]:
        """
        Check for potential HOS violations
        """
        violations = []
        
        # Check if trip would exceed weekly limit
        if trip_request.cycle_used + duty_time > HOS_LIMITS['WEEKLY_LIMIT']:
            violations.append(ERROR_MESSAGES['CYCLE_EXCEEDED'])
        
        # Check daily driving limit
        if drive_time > HOS_LIMITS['DAILY_DRIVE_LIMIT']:
            violations.append(f"Trip requires {drive_time:.1f} hours of driving, exceeding daily limit of {HOS_LIMITS['DAILY_DRIVE_LIMIT']} hours")
        
        # Check daily duty limit
        if duty_time > HOS_LIMITS['DAILY_DUTY_LIMIT']:
            violations.append(f"Trip requires {duty_time:.1f} hours of duty, exceeding daily limit of {HOS_LIMITS['DAILY_DUTY_LIMIT']} hours")
        
        # Check if trip requires multi-day planning
        if route.duration > HOS_LIMITS['DAILY_DRIVE_LIMIT']:
            violations.append("Trip requires multi-day planning with mandatory rest periods")
        
        return violations
    
    def calculate_weekly_hours(self, daily_logs: List[DailyLog]) -> Dict[str, float]:
        """
        Calculate weekly totals from daily logs
        """
        weekly_totals = {
            'total_drive_time': 0.0,
            'total_duty_time': 0.0,
            'days_with_driving': 0
        }
        
        for log in daily_logs:
            weekly_totals['total_drive_time'] += log.total_drive_time
            weekly_totals['total_duty_time'] += log.total_duty_time
            
            if log.total_drive_time > 0:
                weekly_totals['days_with_driving'] += 1
        
        return weekly_totals
    
    def calculate_required_rest_periods(self, route_duration: float) -> List[Dict[str, Any]]:
        """
        Calculate required rest periods for a trip
        """
        rest_periods = []
        
        if route_duration <= HOS_LIMITS['DAILY_DRIVE_LIMIT']:
            # Single day trip - no mandatory rest
            return rest_periods
        
        # Multi-day trip - calculate rest periods
        driving_time_remaining = route_duration
        day = 1
        
        while driving_time_remaining > 0:
            if driving_time_remaining > HOS_LIMITS['DAILY_DRIVE_LIMIT']:
                # Full day of driving
                rest_periods.append({
                    'day': day,
                    'drive_time': HOS_LIMITS['DAILY_DRIVE_LIMIT'],
                    'rest_required': HOS_LIMITS['MANDATORY_REST'],
                    'rest_start': f"After {HOS_LIMITS['DAILY_DRIVE_LIMIT']} hours of driving"
                })
                driving_time_remaining -= HOS_LIMITS['DAILY_DRIVE_LIMIT']
            else:
                # Partial day of driving
                rest_periods.append({
                    'day': day,
                    'drive_time': driving_time_remaining,
                    'rest_required': 0,  # No rest needed after final day
                    'rest_start': "Trip complete"
                })
                driving_time_remaining = 0
            
            day += 1
        
        return rest_periods
    
    def check_cycle_reset_eligibility(self, current_cycle_hours: int, 
                                    last_reset_date: date) -> Dict[str, Any]:
        """
        Check if driver is eligible for cycle reset
        """
        days_since_reset = (date.today() - last_reset_date).days
        
        return {
            'eligible': days_since_reset >= HOS_LIMITS['CYCLE_DAYS'],
            'days_since_reset': days_since_reset,
            'days_until_eligible': max(0, HOS_LIMITS['CYCLE_DAYS'] - days_since_reset),
            'current_cycle_hours': current_cycle_hours,
            'hours_until_limit': HOS_LIMITS['WEEKLY_LIMIT'] - current_cycle_hours
        }
    
    def calculate_available_drive_time(self, trip_request: TripRequest) -> Dict[str, float]:
        """
        Calculate available driving time considering current cycle
        """
        remaining_weekly_hours = HOS_LIMITS['WEEKLY_LIMIT'] - trip_request.cycle_used
        
        return {
            'daily_limit': HOS_LIMITS['DAILY_DRIVE_LIMIT'],
            'weekly_remaining': remaining_weekly_hours,
            'effective_limit': min(HOS_LIMITS['DAILY_DRIVE_LIMIT'], remaining_weekly_hours),
            'duty_limit': HOS_LIMITS['DAILY_DUTY_LIMIT']
        }
    
    def validate_trip_feasibility(self, trip_request: TripRequest, 
                                route_duration: float) -> Dict[str, Any]:
        """
        Validate if trip is feasible given current HOS status
        """
        available_time = self.calculate_available_drive_time(trip_request)
        
        is_feasible = route_duration <= available_time['effective_limit']
        
        result = {
            'feasible': is_feasible,
            'required_drive_time': route_duration,
            'available_drive_time': available_time['effective_limit'],
            'requires_rest': route_duration > HOS_LIMITS['DAILY_DRIVE_LIMIT']
        }
        
        if not is_feasible:
            if route_duration > HOS_LIMITS['DAILY_DRIVE_LIMIT']:
                result['reason'] = 'Trip requires multi-day planning'
                result['recommendation'] = 'Plan mandatory rest periods'
            else:
                result['reason'] = 'Insufficient hours in current cycle'
                result['recommendation'] = 'Wait for cycle reset or reduce trip scope'
        
        return result
