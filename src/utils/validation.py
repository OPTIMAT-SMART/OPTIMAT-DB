"""
Request Validation
----------------
Validation utilities for API requests.
"""

from datetime import datetime
from typing import Dict, Any
from sanic.exceptions import InvalidUsage

def validate_match_request(req_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate provider match request data
    
    Args:
        req_data: Dictionary containing request data
        
    Returns:
        Dict[str, Any]: The validated request data
        
    Raises:
        InvalidUsage: If validation fails
    """
    if not req_data:
        raise InvalidUsage('Request body is empty or invalid JSON')

    required_fields = ['originAddress', 'destinationAddress']
    
    # Check for required fields
    for field in required_fields:
        if field not in req_data:
            raise InvalidUsage(f"Missing required field: {field}")
        if not isinstance(req_data[field], str) or not req_data[field].strip():
            raise InvalidUsage(f"Invalid value for field: {field}")

    # Optional fields with their default values
    optional_fields = {
        'departureTime': None,
        'returnTime': None,
        'eligibility': [],
        'equipment': [],
        'healthConditions': [],
        'needsCompanion': False,
        'allowsSharing': True
    }

    # Create validated data dictionary with required fields
    validated_data = {
        'originAddress': req_data['originAddress'].strip(),
        'destinationAddress': req_data['destinationAddress'].strip()
    }

    # Add optional fields if they exist and are valid
    for field, default in optional_fields.items():
        if field in req_data:
            if field in ['departureTime', 'returnTime'] and req_data[field]:
                try:
                    # Validate datetime format if provided
                    datetime.fromisoformat(req_data[field].replace('Z', '+00:00'))
                    validated_data[field] = req_data[field]
                except ValueError:
                    raise InvalidUsage(f"Invalid datetime format for {field}")
            else:
                validated_data[field] = req_data[field]
        else:
            validated_data[field] = default

    return validated_data

def validate_provider_id(provider_id: str) -> None:
    """
    Validate provider ID format
    
    Args:
        provider_id: Provider identifier to validate
        
    Raises:
        InvalidUsage: If validation fails
    """
    if not provider_id or not provider_id.strip():
        raise InvalidUsage("Provider ID cannot be empty")
    
    if not provider_id.isalnum():
        raise InvalidUsage("Provider ID must be alphanumeric") 