"""
Data classes for structured data handling
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, date


@dataclass
class TripRequest:
    """Input data for trip calculation"""
    current_location: str
    pickup_location: str
    dropoff_location: str
    cycle_used: int  # Hours already used in current cycle
    
    def __post_init__(self):
        # Validate cycle_used is within bounds
        if not (0 <= self.cycle_used <= 70):
            raise ValueError("Cycle used must be between 0 and 70 hours")


@dataclass
class Location:
    """Geographic location data"""
    address: str
    latitude: float
    longitude: float
    
    def to_coords(self) -> List[float]:
        """Return coordinates as [longitude, latitude] for API calls"""
        return [self.longitude, self.latitude]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude
        }


@dataclass
class Stop:
    """Stop information along the route"""
    type: str  # 'rest', 'fuel', 'pickup', 'dropoff'
    location: Location
    time: datetime
    duration: float  # Hours
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'location': {
                'address': self.location.address,
                'coordinates': self.location.to_coords()
            },
            'time': self.time.isoformat(),
            'duration': self.duration,
            'description': self.description
        }


@dataclass
class RouteData:
    """Route calculation results"""
    distance: float  # Miles
    duration: float  # Hours
    coordinates: List[List[float]]  # Route polyline coordinates
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'distance': self.distance,
            'duration': self.duration,
            'coordinates': self.coordinates
        }


@dataclass
class ELDEntry:
    """Individual ELD log entry"""
    status: str  # driving, on_duty, sleeper, off_duty
    start_time: datetime
    end_time: datetime
    location: str
    duration: float  # Hours
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'location': self.location,
            'duration': self.duration
        }


@dataclass
class DailyLog:
    """Daily ELD log sheet"""
    date: date
    entries: List[ELDEntry] = field(default_factory=list)
    total_drive_time: float = 0.0
    total_duty_time: float = 0.0
    
    def add_entry(self, entry: ELDEntry):
        """Add an entry and update totals"""
        self.entries.append(entry)
        if entry.status == 'driving':
            self.total_drive_time += entry.duration
        if entry.status in ['driving', 'on_duty']:
            self.total_duty_time += entry.duration
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date.isoformat(),
            'entries': [entry.to_dict() for entry in self.entries],
            'total_drive_time': self.total_drive_time,
            'total_duty_time': self.total_duty_time
        }


@dataclass
class HOSStatus:
    """Hours of Service compliance status"""
    cycle_used: int
    remaining_hours: int
    drive_time_today: float
    duty_time_today: float
    next_reset: datetime
    violations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cycle_used': self.cycle_used,
            'remaining_hours': self.remaining_hours,
            'drive_time_today': self.drive_time_today,
            'duty_time_today': self.duty_time_today,
            'next_reset': self.next_reset.isoformat(),
            'violations': self.violations
        }


@dataclass
class RouteResponse:
    """Complete response data structure"""
    route: RouteData
    stops: List[Stop]
    fuel_stops: List[Stop]
    eld_logs: List[DailyLog]
    hos_status: HOSStatus
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'route': self.route.to_dict(),
            'stops': [stop.to_dict() for stop in self.stops],
            'fuel_stops': [stop.to_dict() for stop in self.fuel_stops],
            'eld_logs': [log.to_dict() for log in self.eld_logs],
            'hos_status': self.hos_status.to_dict()
        }
