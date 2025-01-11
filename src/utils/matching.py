from datetime import datetime
import pytz
from shapely.geometry import Point, Polygon
import psycopg2
from psycopg2.extras import RealDictCursor
from ..utils.geocoding import geocode_address

# Database connection parameters
DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres.nqqantwjzbymdjqcpkgo',
    'password': 'qMApr1v8VCgY552w',
    'host': 'aws-0-us-west-1.pooler.supabase.com',
    'port': '6543'
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

def get_provider_id():
    """Get list of provider IDs from database"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT provider_id FROM providers WHERE provider_id IS NOT NULL"
            )
            results = cur.fetchall()
            return [result['provider_id'] for result in results if result['provider_id'] is not None]

def parse_time(time_str):
    """Convert time string (HHMM) to hours and minutes"""
    hours = int(time_str[:2])
    minutes = int(time_str[2:])
    return hours, minutes

def check_time_in_range(check_time: datetime, start_time: str, end_time: str) -> bool:
    """Check if a given time falls within a time range"""
    check_hour = check_time.hour
    check_minute = check_time.minute
    
    start_hour = int(start_time[:2])
    start_minute = int(start_time[2:])
    end_hour = int(end_time[:2])
    end_minute = int(end_time[2:])
    
    check_minutes = check_hour * 60 + check_minute
    start_minutes = start_hour * 60 + start_minute
    end_minutes = end_hour * 60 + end_minute
    
    if end_hour >= 24:
        end_minutes = (end_hour - 24) * 60 + end_minute
        if check_minutes < start_minutes:
            check_minutes += 24 * 60
        
    return start_minutes <= check_minutes <= end_minutes

def check_time_match(service_hours: dict, dep_time: str, ret_time: str) -> bool:
    """Check if provider's operating hours match request times"""
    try:
        if not service_hours:
            return False
            
        # Convert ISO format string to datetime object
        dep_time = datetime.fromisoformat(dep_time.replace('Z', '+00:00'))
        ret_time = datetime.fromisoformat(ret_time.replace('Z', '+00:00'))
        
        # Convert UTC to local time
        pacific = pytz.timezone('America/Los_Angeles')
        dep_time = dep_time.astimezone(pacific)
        ret_time = ret_time.astimezone(pacific)
        
        # Check each service hour block
        for hours in service_hours['hours']:
            day_pattern = hours['day']
            
            dep_day_operates = day_pattern[dep_time.weekday()] == '1'
            ret_day_operates = day_pattern[ret_time.weekday()] == '1'
            
            if dep_day_operates and ret_day_operates:
                dep_time_valid = check_time_in_range(dep_time, hours['start'], hours['end'])
                ret_time_valid = check_time_in_range(ret_time, hours['start'], hours['end'])
                
                if dep_time_valid and ret_time_valid:
                    return True
                    
        return False
        
    except Exception as e:
        print(f"Error in check_time_match: {e}")
        return False

async def check_area_match(service_zone: dict, org_coords: tuple, dest_coords: tuple) -> bool:
    """Check if coordinates fall within service zone"""
    try:
        if not service_zone or not org_coords or not dest_coords:
            return False
            
        coordinates = service_zone['features'][0]['geometry']['coordinates']
        polygon = Polygon(coordinates[0])
        
        org_point = Point(*org_coords)
        dest_point = Point(*dest_coords)
        
        return polygon.contains(org_point) and polygon.contains(dest_point)
        
    except Exception as e:
        print(f"Error in check_area_match: {e}")
        return False

def modes_match_eligibility(myEligible, id_value):
    """Check if user's eligibility matches provider requirements"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT eligibility_req FROM providers WHERE provider_id = %s",
                    (id_value,)
                )
                result = cur.fetchone()
                
                if not result:
                    return False
                    
                return result['eligibility_req'] == 'ada-approved'
    except Exception as e:
        print(f"Error in modes_match_eligibility: {e}")
        return False

def modes_match_needs(myEquipment, myHealthCond, myCompanion, mySharing, id_value):
    """Dummy function to check if provider can accommodate user's needs"""
    print(f"Checking needs match for provider {id_value}")
    # Dummy logic: assume all providers can accommodate all needs
    return True

def modes_match_fixed_route(reqOrgAddr, reqDesAddr, reqDepTime, reqRetTime, id_value):
    """Dummy function to check if fixed route service is available"""
    print(f"Checking fixed route match for provider {id_value}")
    # Dummy logic: assume fixed route is always available
    return True

def mode_full_info(providerID):
    """Get full provider information from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM providers WHERE provider_id = %s",
                    (providerID,)
                )
                return cur.fetchall()
    except Exception as e:
        print(f"Error in mode_full_info: {e}")
        return None

def write_error_message(request, endpoint, error):
    """Dummy function to log errors"""
    print(f"ERROR at {endpoint}: {str(error)}")
    print(f"Request data: {request.json if hasattr(request, 'json') else 'No JSON data'}")