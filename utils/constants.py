"""
Constants for ELD and HOS (Hours of Service) regulations
"""
import os

# Hours of Service Limits
HOS_LIMITS = {
    'DAILY_DRIVE_LIMIT': 11,      # Maximum hours of driving per day
    'DAILY_DUTY_LIMIT': 14,       # Maximum hours of duty per day
    'WEEKLY_LIMIT': 70,           # Maximum hours in 7/8 days
    'CYCLE_DAYS': 8,              # Reset cycle days
    'MANDATORY_REST': 10,         # Mandatory rest period (hours)
    'BREAK_AFTER_HOURS': 8,       # Break required after 8 hours
    'BREAK_DURATION': 0.5,        # 30-minute break duration
}

# ELD Duty Statuses
DUTY_STATUS = {
    'DRIVING': 'driving',
    'ON_DUTY': 'on_duty',
    'SLEEPER': 'sleeper',
    'OFF_DUTY': 'off_duty',
}

# Route calculation constants
ROUTE_CONSTANTS = {
    'FUEL_STOP_INTERVAL': 1000,   # Miles between fuel stops
    'AVERAGE_SPEED': 55,          # Average highway speed (mph)
    'PICKUP_DURATION': 1.0,       # Hours for pickup
    'DROPOFF_DURATION': 1.0,      # Hours for dropoff
    'FUEL_STOP_DURATION': 0.5,    # Hours for refueling
}

# API Keys
OPENROUTESERVICE_API_KEY = os.getenv('OPENROUTESERVICE_API_KEY', 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjczZjIyNjNlZGMwMjQ5YTBhMzdiZjJhNDNjZjAwMDYwIiwiaCI6Im11cm11cjY0In0=')

# External API URLs
API_URLS = {
    'OPENROUTE_BASE': 'https://api.openrouteservice.org/v2',
    'NOMINATIM_BASE': 'https://nominatim.openstreetmap.org',
}

# Error messages
ERROR_MESSAGES = {
    'INVALID_LOCATION': 'Invalid location provided',
    'ROUTE_NOT_FOUND': 'Route could not be calculated',
    'HOS_VIOLATION': 'Hours of Service violation detected',
    'API_ERROR': 'External API error',
    'CYCLE_EXCEEDED': 'Weekly cycle limit exceeded',
}
