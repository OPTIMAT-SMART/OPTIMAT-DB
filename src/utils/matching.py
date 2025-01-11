from datetime import datetime
import pytz
from shapely.geometry import Point, Polygon
from shapely import prepare
from typing import Dict, Tuple, List
from dataclasses import dataclass

@dataclass
class TimeRange:
    """Represents a time range with start and end times in minutes"""
    start: int
    end: int

    @classmethod
    def from_string(cls, start: str, end: str) -> 'TimeRange':
        """Create TimeRange from HHMM format strings"""
        try:
            start_mins = int(start[:2]) * 60 + int(start[2:])
            end_mins = int(end[:2]) * 60 + int(end[2:])
            return cls(start_mins, end_mins)
        except (ValueError, TypeError) as e:
            print(f"Error parsing time strings: start='{start}', end='{end}', Error: {e}")
            raise

def convert_time_to_minutes(time: datetime) -> int:
    """Convert datetime to minutes since midnight"""
    return time.hour * 60 + time.minute

def check_time_in_range(check_time: datetime, time_range: TimeRange) -> bool:
    """Check if the given time is within the range"""
    check_mins = convert_time_to_minutes(check_time)

    if time_range.end < time_range.start:
        # Overnight range (e.g., 22:00 to 06:00)
        return check_mins >= time_range.start or check_mins <= time_range.end
    else:
        return time_range.start <= check_mins <= time_range.end

def check_time_match(service_hours: Dict[str, List[Dict[str, str]]], dep_time: str, ret_time: str) -> bool:
    """
    Check if departure and return times match the service hours.
    
    service_hours format: {"hours": [{"day": "1111100", "start": "0706", "end": "2205"}]}
    day pattern: Monday to Sunday, 1=service available, 0=no service
    time format: "HHMM" in 24-hour format
    """
    try:
        if not service_hours or 'hours' not in service_hours:
            return False

        # Convert times to datetime objects and Pacific time
        pacific = pytz.timezone('America/Los_Angeles')
        dep_dt = datetime.fromisoformat(dep_time.replace('Z', '+00:00')).astimezone(pacific)
        ret_dt = datetime.fromisoformat(ret_time.replace('Z', '+00:00')).astimezone(pacific)

        # Get weekday indices (0=Monday, 6=Sunday)
        dep_weekday = dep_dt.weekday()
        ret_weekday = ret_dt.weekday()

        # Convert times to minutes for comparison
        dep_minutes = dep_dt.hour * 60 + dep_dt.minute
        ret_minutes = ret_dt.hour * 60 + ret_dt.minute

        # Check each service hours entry
        for hours in service_hours['hours']:
            # Verify day pattern format
            day_pattern = hours.get('day', '')
            if len(day_pattern) != 7:
                continue

            # Check if service is available on both days
            if day_pattern[dep_weekday] != '1' or day_pattern[ret_weekday] != '1':
                continue

            # Convert service hours to minutes
            try:
                start_time = hours['start']
                end_time = hours['end']
                start_minutes = int(start_time[:2]) * 60 + int(start_time[2:])
                end_minutes = int(end_time[:2]) * 60 + int(end_time[2:])
            except (ValueError, IndexError):
                continue

            # Check if both times fall within service hours
            if start_minutes <= dep_minutes <= end_minutes and start_minutes <= ret_minutes <= end_minutes:
                return True

        return False

    except Exception as e:
        print(f"Error in check_time_match: {str(e)}")
        return False

class ServiceZoneMatcher:
    """Optimized service zone matching with prepared geometries"""
    def __init__(self, service_zone: Dict):
        try:
            coordinates = service_zone['features'][0]['geometry']['coordinates']
            self.polygon = Polygon(coordinates[0])
            self.prepared_polygon = prepare(self.polygon)  # Optimize for repeated contains() calls
        except (IndexError, KeyError, TypeError) as e:
            print(f"Error initializing ServiceZoneMatcher: {e}")
            raise

    def check_points(self, org_coords: Tuple[float, float], dest_coords: Tuple[float, float]) -> bool:
        """Check if both points are within the service zone"""
        try:
            org_point = Point(*org_coords)
            dest_point = Point(*dest_coords)
            in_org = self.prepared_polygon.contains(org_point)
            in_dest = self.prepared_polygon.contains(dest_point)
            print(f"Origin within service zone: {in_org}, Destination within service zone: {in_dest}")
            return in_org and in_dest
        except Exception as e:
            print(f"Error in check_points: {e}")
            return False

async def check_area_match(service_zone: Dict, 
                           org_coords: Tuple[float, float], 
                           dest_coords: Tuple[float, float]) -> bool:
    """Wrapper for service zone matching"""
    try:
        if not service_zone or not org_coords or not dest_coords:
            print("Invalid service_zone or coordinates")
            return False

        matcher = ServiceZoneMatcher(service_zone)
        return matcher.check_points(org_coords, dest_coords)

    except Exception as e:
        print(f"Error in check_area_match: {e}")
        return False
    
