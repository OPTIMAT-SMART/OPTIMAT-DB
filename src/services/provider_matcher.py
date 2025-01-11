"""
Provider Matching Service
------------------------
This module handles the logic for matching transportation providers
based on user requirements and preferences.
"""

from typing import Dict, List, Any
from datetime import datetime
from src.utils.matching import check_time_match, check_area_match
from src.utils.geocoding import geocode_address
from src.utils.config import config

class ProviderMatchError(Exception):
    """Base class for provider matching errors"""
    def __init__(self, message: str, error_code: str, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

async def find_matching_providers(conn, req: Dict[str, Any], table: str = 'providers') -> List[Dict]:
    """Asynchronous provider matching"""
    try:
        # Validate and convert times once
        dep_time = datetime.fromisoformat(req['departureTime'].replace('Z', '+00:00')) if req.get('departureTime') else None
        ret_time = datetime.fromisoformat(req['returnTime'].replace('Z', '+00:00')) if req.get('returnTime') else None

        if dep_time and ret_time and ret_time <= dep_time:
            raise ProviderMatchError(
                "Return time must be after departure time",
                "INVALID_TIME_RANGE",
                {'departure': dep_time.isoformat(), 'return': ret_time.isoformat()}
            )

        # Geocode addresses once
        origin_coords = geocode_address(req['originAddress'])
        destination_coords = geocode_address(req['destinationAddress'])

        if not origin_coords or not destination_coords:
            raise ProviderMatchError(
                "Could not geocode one or both addresses",
                "GEOCODING_ERROR",
                {'originAddress': req['originAddress'], 'destinationAddress': req['destinationAddress']}
            )

        # Fetch all providers in one query
        query = f"""
            SELECT 
                provider_id,
                provider_name,
                provider_type,
                service_hours,
                service_zone
            FROM {config.DB_SCHEMA}.{table}
            WHERE provider_id IS NOT NULL
              AND service_zone IS NOT NULL
              AND service_hours IS NOT NULL
        """
        providers = await conn.fetch(query)

        if not providers:
            raise ProviderMatchError("No providers found", "NO_PROVIDERS")

        # Match providers efficiently
        matching_providers = []
        for provider in providers:
            try:
                provider_dict = dict(provider)

                if not check_time_match(
                    provider_dict['service_hours'],
                    req.get('departureTime'),
                    req.get('returnTime')
                ):
                    continue

                if not await check_area_match(
                    provider_dict['service_zone'],
                    origin_coords,
                    destination_coords
                ):
                    continue

                matching_providers.append({
                    "ID": provider_dict['provider_id'],
                    "Provider": provider_dict['provider_name'],
                    "Type": provider_dict['provider_type']
                })

            except Exception as e:
                print(f"Error checking provider {provider['provider_id']}: {e}")
                continue

        if not matching_providers:
            raise ProviderMatchError(
                "No providers match the criteria",
                "NO_MATCHES",
                {'criteria': req}
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

async def _check_provider_matches(conn, provider_id: str, req: Dict, table: str = 'providers') -> bool:
    """Check if a provider matches all requirements"""
    # Get all required fields in one query
    query = f"""
        SELECT service_hours, service_zone
        FROM {config.DB_SCHEMA}.{table}
        WHERE provider_id = $1
    """
    result = await conn.fetchrow(query, provider_id)

    if not result:
        return False

    # Check time match
    if not check_time_match(result['service_hours'], req.get('departureTime'), req.get('returnTime')):
        return False

    # Check area match
    if not check_area_match(result['service_zone'], req['originAddress'], req['destinationAddress']):
        return False

    return True