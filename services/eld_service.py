"""
ELD (Electronic Logging Device) service for generating duty logs
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta, date

from utils.data_classes import TripRequest, Stop, RouteData, ELDEntry, DailyLog
from utils.constants import DUTY_STATUS, HOS_LIMITS, ROUTE_CONSTANTS

logger = logging.getLogger(__name__)


class ELDService:
    """
    Service for generating ELD logs based on trip data
    """
    
    def generate_logs(self, route_data: Dict[str, Any], trip_request: TripRequest) -> List[DailyLog]:
        """
        Generate ELD logs for the entire trip
        
        Returns list of daily logs covering the trip duration
        """
        try:
            route = route_data['route']
            stops = route_data['stops']
            fuel_stops = route_data['fuel_stops']
            
            # Calculate trip timeline
            start_time = datetime.now()
            daily_logs = []
            
            # Generate logs day by day
            current_time = start_time
            current_date = start_time.date()
            current_log = DailyLog(date=current_date)
            
            # Process each stop in chronological order
            all_stops = self._merge_and_sort_stops(stops, fuel_stops)
            
            for i, stop in enumerate(all_stops):
                # Calculate driving time to this stop
                if i == 0:
                    drive_time = 0
                else:
                    prev_stop = all_stops[i - 1]
                    drive_time = self._calculate_drive_time_between_stops(prev_stop, stop, route)
                
                # Add driving entry if there was driving time
                if drive_time > 0:
                    current_time, current_log, daily_logs = self._add_driving_entry(
                        current_time, current_log, daily_logs, drive_time, 
                        prev_stop.location.address if i > 0 else "Start Location"
                    )
                
                # Add stop entry (on-duty or off-duty)
                current_time, current_log, daily_logs = self._add_stop_entry(
                    current_time, current_log, daily_logs, stop
                )
            
            # Add final log if it has entries
            if current_log.entries:
                daily_logs.append(current_log)
            
            return daily_logs
            
        except Exception as e:
            logger.error(f"ELD log generation failed: {str(e)}")
            raise Exception(f"Could not generate ELD logs: {str(e)}")
    
    def _merge_and_sort_stops(self, stops: List[Stop], fuel_stops: List[Stop]) -> List[Stop]:
        """
        Merge and sort all stops by time/distance
        """
        # For now, we'll use a simple approach based on stop type order
        # In production, you'd sort by actual time/distance
        
        sorted_stops = []
        
        # Add pickup stop first
        pickup_stops = [s for s in stops if s.type == 'pickup']
        sorted_stops.extend(pickup_stops)
        
        # Add fuel stops (distributed along route)
        sorted_stops.extend(fuel_stops)
        
        # Add rest stops
        rest_stops = [s for s in stops if s.type == 'rest']
        sorted_stops.extend(rest_stops)
        
        # Add dropoff stop last
        dropoff_stops = [s for s in stops if s.type == 'dropoff']
        sorted_stops.extend(dropoff_stops)
        
        return sorted_stops
    
    def _calculate_drive_time_between_stops(self, prev_stop: Stop, current_stop: Stop, route: RouteData) -> float:
        """
        Calculate driving time between two stops
        """
        # Simplified calculation - in production, you'd use actual route segments
        # For now, assume equal distribution of time
        total_stops = 5  # Approximate number of stops
        segment_time = route.duration / total_stops
        
        # Adjust based on stop types
        if prev_stop.type == 'pickup':
            return segment_time * 0.2  # Short drive after pickup
        elif current_stop.type == 'dropoff':
            return segment_time * 0.3  # Longer drive to dropoff
        else:
            return segment_time * 0.5  # Regular driving segments
    
    def _add_driving_entry(self, current_time: datetime, current_log: DailyLog, 
                          daily_logs: List[DailyLog], drive_time: float, 
                          location: str) -> tuple:
        """
        Add driving entry to the log, handling day transitions
        """
        end_time = current_time + timedelta(hours=drive_time)
        
        # Check if driving spans multiple days
        if current_time.date() != end_time.date():
            # Split driving across days
            remaining_time = drive_time
            
            while remaining_time > 0:
                # Calculate time until end of current day
                end_of_day = datetime.combine(current_time.date(), datetime.max.time())
                time_in_day = (end_of_day - current_time).total_seconds() / 3600
                
                if time_in_day >= remaining_time:
                    # Driving finishes in current day
                    entry = ELDEntry(
                        status=DUTY_STATUS['DRIVING'],
                        start_time=current_time,
                        end_time=current_time + timedelta(hours=remaining_time),
                        location=location,
                        duration=remaining_time
                    )
                    current_log.add_entry(entry)
                    current_time += timedelta(hours=remaining_time)
                    remaining_time = 0
                else:
                    # Driving continues to next day
                    entry = ELDEntry(
                        status=DUTY_STATUS['DRIVING'],
                        start_time=current_time,
                        end_time=end_of_day,
                        location=location,
                        duration=time_in_day
                    )
                    current_log.add_entry(entry)
                    daily_logs.append(current_log)
                    
                    # Start new day
                    current_time = datetime.combine(current_time.date() + timedelta(days=1), datetime.min.time())
                    current_log = DailyLog(date=current_time.date())
                    remaining_time -= time_in_day
        else:
            # Driving is within same day
            entry = ELDEntry(
                status=DUTY_STATUS['DRIVING'],
                start_time=current_time,
                end_time=end_time,
                location=location,
                duration=drive_time
            )
            current_log.add_entry(entry)
            current_time = end_time
        
        return current_time, current_log, daily_logs
    
    def _add_stop_entry(self, current_time: datetime, current_log: DailyLog, 
                       daily_logs: List[DailyLog], stop: Stop) -> tuple:
        """
        Add stop entry to the log
        """
        # Determine duty status based on stop type
        if stop.type in ['pickup', 'dropoff', 'fuel']:
            status = DUTY_STATUS['ON_DUTY']
        elif stop.type == 'rest':
            status = DUTY_STATUS['SLEEPER']
        else:
            status = DUTY_STATUS['OFF_DUTY']
        
        end_time = current_time + timedelta(hours=stop.duration)
        
        # Check if stop spans multiple days
        if current_time.date() != end_time.date():
            # Split stop across days
            remaining_time = stop.duration
            
            while remaining_time > 0:
                # Calculate time until end of current day
                end_of_day = datetime.combine(current_time.date(), datetime.max.time())
                time_in_day = (end_of_day - current_time).total_seconds() / 3600
                
                if time_in_day >= remaining_time:
                    # Stop finishes in current day
                    entry = ELDEntry(
                        status=status,
                        start_time=current_time,
                        end_time=current_time + timedelta(hours=remaining_time),
                        location=stop.location.address,
                        duration=remaining_time
                    )
                    current_log.add_entry(entry)
                    current_time += timedelta(hours=remaining_time)
                    remaining_time = 0
                else:
                    # Stop continues to next day
                    entry = ELDEntry(
                        status=status,
                        start_time=current_time,
                        end_time=end_of_day,
                        location=stop.location.address,
                        duration=time_in_day
                    )
                    current_log.add_entry(entry)
                    daily_logs.append(current_log)
                    
                    # Start new day
                    current_time = datetime.combine(current_time.date() + timedelta(days=1), datetime.min.time())
                    current_log = DailyLog(date=current_time.date())
                    remaining_time -= time_in_day
        else:
            # Stop is within same day
            entry = ELDEntry(
                status=status,
                start_time=current_time,
                end_time=end_time,
                location=stop.location.address,
                duration=stop.duration
            )
            current_log.add_entry(entry)
            current_time = end_time
        
        return current_time, current_log, daily_logs
    
    def _should_start_new_day(self, current_time: datetime, entry_duration: float) -> bool:
        """
        Check if a new day should be started based on time
        """
        end_time = current_time + timedelta(hours=entry_duration)
        return current_time.date() != end_time.date()
    
    def validate_hos_compliance(self, daily_logs: List[DailyLog]) -> List[str]:
        """
        Validate HOS compliance for generated logs
        """
        violations = []
        
        for log in daily_logs:
            # Check daily driving limit
            if log.total_drive_time > HOS_LIMITS['DAILY_DRIVE_LIMIT']:
                violations.append(f"Daily driving limit exceeded on {log.date}: {log.total_drive_time:.1f} hours")
            
            # Check daily duty limit
            if log.total_duty_time > HOS_LIMITS['DAILY_DUTY_LIMIT']:
                violations.append(f"Daily duty limit exceeded on {log.date}: {log.total_duty_time:.1f} hours")
        
        return violations
