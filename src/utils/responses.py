"""
Response Utilities
----------------
Standardized response formatting for the API.
"""

from typing import Any, Dict, Optional
from sanic.response import JSONResponse

def success_response(
    data: Any = None,
    message: str = "Success",
    status: int = 200
) -> JSONResponse:
    """Create a standardized success response"""
    return JSONResponse(
        {
            'status': 'SUCCESS',
            'data': data,
            'message': message
        },
        status=status
    )

def error_response(
    message: str,
    error_code: str,
    details: Optional[Dict] = None,
    status: int = 400
) -> JSONResponse:
    """Create a standardized error response"""
    return JSONResponse(
        {
            'status': 'ERROR',
            'error': message,
            'error_code': error_code,
            'details': details
        },
        status=status
    ) 