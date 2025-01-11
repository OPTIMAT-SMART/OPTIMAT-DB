from datetime import datetime
from shapely.geometry import Point, shape
from typing import Dict, Tuple, List
from dataclasses import dataclass
import json

def check_time_match(service_hours: str, dep_time: str, ret_time: str) -> bool:
    """
    Checks if both departure and return times fall within at least one of 
    the service-hour schedules, based on day-of-week and start-end times.

    :param service_hours: JSON string like:
        {
          "hours": [
            {
              "day": "1111100",
              "end": "2414",
              "start": "0444"
            },
            {
              "day": "0000010",
              "end": "2303",
              "start": "0550"
            }
          ]
        }
    :param dep_time: e.g. "2024-03-20T09:30:00-07:00" (ISO 8601 string)
    :param ret_time: e.g. "2024-03-20T14:45:00-07:00" (ISO 8601 string)
    :return: True if dep_time and ret_time each match at least one schedule, otherwise False.
    """

    # 1) Parse the JSON string into a Python dict
    try:
        parsed_service_hours = json.loads(service_hours)
    except json.JSONDecodeError as e:
        print(f"Error parsing service_hours JSON: {e}")
        return False

    # 2) Convert dep_time and ret_time from ISO 8601 strings to datetime objects
    try:
        dep_dt = datetime.fromisoformat(dep_time)
        ret_dt = datetime.fromisoformat(ret_time)
    except ValueError as e:
        print(f"Error parsing ISO datetime: {e}")
        return False

    # 3) Extract day-of-week (Mon=0 ... Sun=6)
    dep_dow = dep_dt.weekday()
    ret_dow = ret_dt.weekday()

    # 4) Convert HH:MM to an integer HHMM for easy comparison
    dep_int = dep_dt.hour * 100 + dep_dt.minute
    ret_int = ret_dt.hour * 100 + ret_dt.minute

    def schedule_matches_day_time(schedule, dow, time_hhmm) -> bool:
        """
        Returns True if the given day-of-week/time matches this schedule's day bit
        and falls between start_int and end_int (supporting >2400).
        """
        day_pattern = schedule["day"]    # e.g. "1111100"
        start_str   = schedule["start"]  # e.g. "0444"
        end_str     = schedule["end"]    # e.g. "2414"

        # Check if day-of-week bit is set to '1'
        # Make sure dow is int (0..6) and we're indexing day_pattern as day_pattern[dow]
        if day_pattern[dow] != '1':
            return False

        # Convert start/end to int for comparison
        start_int = int(start_str)
        end_int   = int(end_str)

        # If end >= 2400, interpret it as crossing midnight
        if end_int >= 2400:
            # Convert to total minutes to handle crossing midnight
            start_minutes  = (start_int // 100) * 60 + (start_int % 100)
            end_minutes    = (end_int // 100) * 60 + (end_int % 100)
            current_minutes = (time_hhmm // 100) * 60 + (time_hhmm % 100)

            # If current_minutes >= start_minutes (same day) or 
            #     current_minutes <= (end_minutes - 1440) (after midnight next day)
            if current_minutes >= start_minutes:
                return True
            else:
                # e.g., "2414" means 00:14 next day, so end_minutes - 1440 = 14 minutes
                if current_minutes <= (end_minutes - 1440):
                    return True
            return False
        else:
            # Normal same-day comparison
            return (start_int <= time_hhmm <= end_int)

    # 5) Check if departure time matches at least one schedule
    schedules = parsed_service_hours.get("hours", [])
    dep_ok = any(schedule_matches_day_time(sched, dep_dow, dep_int) for sched in schedules)
    # 6) Check if return time matches at least one schedule
    ret_ok = any(schedule_matches_day_time(sched, ret_dow, ret_int) for sched in schedules)

    return dep_ok and ret_ok


async def check_area_match(
    service_zone: str,
    org_coords: Tuple[float, float],
    dest_coords: Tuple[float, float]
) -> bool:
    """
    Given a GeoJSON FeatureCollection (as a string) and two (lng, lat) tuples 
    for origin and destination, return True if both are inside the first
    polygon in the GeoJSON, else False.

    :param service_zone: A string containing valid GeoJSON, e.g.
        {
          "type":"FeatureCollection",
          "features": [
            {
              "type":"Feature",
              "geometry": {
                "type":"Polygon",
                "coordinates":[
                  [
                    [-122.374009,38.0464463], 
                    ...
                  ]
                ]
              }
            }
          ]
        }
    :param org_coords: (longitude, latitude) for the origin
    :param dest_coords: (longitude, latitude) for the destination
    :return: True if both points lie within the polygon; otherwise False.
    """

    # 1. Parse the GeoJSON string
    try:
        parsed_geojson = json.loads(service_zone)
    except json.JSONDecodeError as err:
        print(f"Error parsing GeoJSON: {err}")
        return False

    # 2. Extract the first feature's geometry
    features = parsed_geojson.get("features", [])
    if not features:
        print("No features found in GeoJSON.")
        return False

    geometry = features[0].get("geometry", None)
    if not geometry:
        print("No geometry found in the first feature.")
        return False

    # 3. Convert the GeoJSON geometry to a Shapely polygon/shape
    zone_shape = shape(geometry)

    # 4. Create Shapely Points for origin and destination
    origin_point = Point(org_coords[0], org_coords[1])  # (lng, lat)
    dest_point   = Point(dest_coords[0], dest_coords[1])

    # 5. Check if both points fall within the polygon
    return origin_point.within(zone_shape) and dest_point.within(zone_shape)
