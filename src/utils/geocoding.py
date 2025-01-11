from geopy.geocoders import Nominatim
from functools import lru_cache
import time
from typing import Optional, Tuple

class GeocoderService:
    def __init__(self):
        self.nominatim = Nominatim(user_agent="optimat_app")
        self.delay = 1.1
        self.last_call = 0
        
    def _respect_rate_limit(self) -> None:
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call
        if time_since_last_call < self.delay:
            time.sleep(self.delay - time_since_last_call)
        self.last_call = time.time()
    
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode address with rate limiting"""
        try:
            self._respect_rate_limit()
            location = self.nominatim.geocode(address)
            return (location.longitude, location.latitude) if location else None
            
        except Exception as e:
            print(f"Geocoding error for {address}: {e}")
            return None

# Single instance pattern
_geocoder = GeocoderService()

@lru_cache(maxsize=1000)
def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """Cached geocoding results"""
    return _geocoder.geocode(address)