"""
Provider Matching Service
------------------------
This module handles the logic for matching transportation providers
based on user requirements and preferences.
"""

from typing import Dict, List, Any
from psycopg2.extensions import cursor
from datetime import datetime
import pytz

from ..utils.matching import check_time_match, check_area_match
from ..utils.geocoding import geocode_address

class ProviderMatchError(Exception):
    """Base class for provider matching errors"""
    def __init__(self, message: str, error_code: str, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

def find_matching_providers(cur: cursor, req: Dict, table: str = 'providers') -> List[Dict]:
    """
    Find providers that match the given requirements.
    
    Args:
        cur: Database cursor
        req: Request data containing user requirements
        table: Table name to query ('providers' or 'providers_mock')
        
    Returns:
        List of matching providers with their details
        
    Raises:
        ProviderMatchError: When matching fails with specific reason
    """
    
    try:
        # Validate times
        dep_time = datetime.fromisoformat(req['departureTime'].replace('Z', '+00:00'))
        ret_time = datetime.fromisoformat(req['returnTime'].replace('Z', '+00:00'))
        
        if ret_time <= dep_time:
            raise ProviderMatchError(
                "Return time must be after departure time",
                "INVALID_TIME_RANGE",
                {
                    'departure': dep_time.isoformat(),
                    'return': ret_time.isoformat()
                }
            )
        
        # Geocode addresses once at the start
        org_coords = geocode_address(req['originAddress'])
        dest_coords = geocode_address(req['destinationAddress'])
        
        if not org_coords or not dest_coords:
            raise ProviderMatchError(
                "Could not geocode one or both addresses",
                "GEOCODING_ERROR",
                {
                    'origin': req['originAddress'],
                    'destination': req['destinationAddress']
                }
            )
        
        # Get all provider data in one query
        cur.execute(f"""
            SELECT provider_id, provider_name, provider_type, service_hours, service_zone
            FROM atccc.{table}
            WHERE provider_id IS NOT NULL
        """)
        providers = cur.fetchall()
        
        if not providers:
            raise ProviderMatchError(
                "No providers found in the system",
                "NO_PROVIDERS"
            )
        
        matching_providers = []
        for provider in providers:
            try:
                # Check time match
                if not check_time_match(provider['service_hours'], req['departureTime'], req['returnTime']):
                    continue
                    
                # Check area match with pre-geocoded coordinates
                if not check_area_match(provider['service_zone'], org_coords, dest_coords):
                    continue
                    
                matching_providers.append({
                    "ID": provider['provider_id'],
                    "Provider": provider['provider_name'],
                    "Type": provider['provider_type']
                })
            except Exception as e:
                print(f"Error checking provider {provider['provider_id']}: {e}")
                continue
        
        if not matching_providers:
            raise ProviderMatchError(
                "No providers match the given criteria",
                "NO_MATCHES",
                {
                    'criteria': {
                        'eligibility': req['eligibility'],
                        'equipment': req['equipment'],
                        'healthConditions': req['healthConditions'],
                        'needsCompanion': req['needsCompanion'],
                        'allowsSharing': req['allowsSharing']
                    }
                }
            )
        
        return matching_providers
    
    except ProviderMatchError:
        raise
    
    except Exception as e:
        raise ProviderMatchError(
            f"Provider matching failed: {str(e)}",
            "MATCH_PROCESS_ERROR",
            {'original_error': str(e)}
        )

def _check_provider_matches(cur: cursor, provider_id: str, req: Dict, table: str = 'providers') -> bool:
    """Check if a provider matches all requirements"""
    # Get all required fields in one query
    cur.execute(
        f"""SELECT service_hours, service_zone
        FROM atccc.{table} 
        WHERE provider_id = %s""",
        (provider_id,)
    )
    result = cur.fetchone()
    
    # Check time match
    if not check_time_match(result['service_hours'], req['departureTime'], req['returnTime']):
        return False
    
    # Check area match
    if not check_area_match(result['service_zone'], req['originAddress'], req['destinationAddress']):
        return False
        
    return True