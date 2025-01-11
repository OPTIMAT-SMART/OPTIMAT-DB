"""
Shared Exceptions
---------------
Common exception classes used across the application.
"""

from typing import Dict, Any

class ProviderMatchError(Exception):
    """Base class for provider matching errors"""
    def __init__(self, message: str, error_code: str, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message) 