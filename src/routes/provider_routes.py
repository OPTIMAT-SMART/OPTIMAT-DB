"""
Provider Routes
---------------
Handles all provider-related API endpoints.
"""

from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from sanic.exceptions import NotFound, InvalidUsage

from src.utils.exceptions import ProviderMatchError
from src.services.provider_matcher import find_matching_providers
from src.utils.responses import success_response, error_response
from src.utils.validation import validate_match_request
from src.utils.db import database
from src.utils.config import config

def setup_provider_routes(blueprint: Blueprint) -> None:
    """Setup provider routes on the given blueprint"""
    
    @blueprint.get("/providers")
    async def get_providers(request: Request) -> json:
        """Get all providers"""
        try:
            async with database.get_db_connection() as conn:
                table = 'providers_mock' if request.app.config.USE_MOCK_DATA else 'providers'
                
                query = f"SELECT * FROM {config.DB_SCHEMA}.{table} ORDER BY provider_id"
                results = await conn.fetch(query)
                
                providers = [dict(row) for row in results]
                
                return success_response(
                    data=providers,
                    message=f"Found {len(providers)} providers"
                )
                
        except Exception as e:
            return error_response(
                message="Internal server error",
                error_code='SERVER_ERROR',
                details={'error': str(e)},
                status=500
            )

    @blueprint.post("/providers/match")
    async def match_providers(request: Request) -> json:
        """Match providers based on request criteria"""
        try:
            # Validate request data and get validated data
            validated_data = validate_match_request(request.json)
            
            table = 'providers_mock' if request.app.config.USE_MOCK_DATA else 'providers'

            async with database.get_db_connection() as conn:
                # Find matching providers using validated data
                matches = await find_matching_providers(
                    conn,
                    req=validated_data,
                    table=table
                )
            
            return success_response(
                data=matches,
                message=f"Found {len(matches)} matching providers"
            )
            
        except InvalidUsage as e:
            return error_response(
                message="Invalid request",
                error_code='INVALID_REQUEST',
                details={'error': str(e)},
                status=400
            )
            
        except ProviderMatchError as e:
            return error_response(
                message="Provider matching failed",
                error_code=e.error_code,
                details={'error': e.message, 'details': e.details},
                status=400
            )
            
        except Exception as e:
            return error_response(
                message="Internal server error",
                error_code='SERVER_ERROR',
                details={'error': str(e)},
                status=500
            )

    @blueprint.get("/providers/<provider_id:int>")
    async def get_provider(request: Request, provider_id: int) -> json:
        """Get a specific provider by ID"""
        try:
            async with database.get_db_connection() as conn:
                table = 'providers_mock' if request.app.config.USE_MOCK_DATA else 'providers'
                
                query = f"SELECT * FROM {config.DB_SCHEMA}.{table} WHERE provider_id = $1"
                result = await conn.fetchrow(query, provider_id)
                
                if not result:
                    raise NotFound(f"Provider with ID {provider_id} not found")
                
                return success_response(
                    data=dict(result),
                    message=f"Provider {provider_id} retrieved successfully"
                )
                
        except NotFound as e:
            return error_response(
                message="Provider not found",
                error_code='NOT_FOUND',
                details={'error': str(e)},
                status=404
            )
            
        except Exception as e:
            return error_response(
                message="Internal server error",
                error_code='SERVER_ERROR',
                details={'error': str(e)},
                status=500
            ) 