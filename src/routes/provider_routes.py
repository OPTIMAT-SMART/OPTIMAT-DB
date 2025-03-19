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

async def get_all_providers() -> tuple:
    """Get all providers from database"""
    try:
        async with database.get_db_connection() as conn:
            table = 'providers_mock' if config.USE_MOCK_DATA else 'providers'
            
            query = f"SELECT * FROM {config.DB_SCHEMA}.{table} ORDER BY provider_id"
            results = await conn.fetch(query)
            
            providers = [dict(row) for row in results]
            return providers, None
            
    except Exception as e:
        return None, str(e)

async def get_provider_by_id(provider_id: int) -> tuple:
    """Get a specific provider by ID"""
    try:
        async with database.get_db_connection() as conn:
            table = 'providers_mock' if config.USE_MOCK_DATA else 'providers'
            
            query = f"""
                SELECT provider_id, provider_name, contacts, provider_org, 
                       service_hours, fare, booking, 
                       eligibility_req, schedule_type, routing_type, provider_type
                FROM {config.DB_SCHEMA}.{table} 
                WHERE provider_id = $1
            """
            result = await conn.fetchrow(query, provider_id)
            
            if not result:
                return None, f"Provider with ID {provider_id} not found"
            
            return dict(result), None
            
    except Exception as e:
        return None, str(e)

async def get_provider_info_by_name(provider_name: str) -> tuple:
    """Get provider information by name"""
    try:
        async with database.get_db_connection() as conn:
            table = 'providers_mock' if config.USE_MOCK_DATA else 'providers'
            
            query = f"""
                SELECT provider_id, provider_name, contacts, provider_org, 
                       service_hours, fare, booking, 
                       eligibility_req, schedule_type, routing_type, provider_type
                FROM {config.DB_SCHEMA}.{table} 
                WHERE provider_name ILIKE $1
                ORDER BY provider_id
            """
            results = await conn.fetch(query, f'%{provider_name}%')
            
            if not results:
                return None, f"No providers found matching name '{provider_name}'"
            
            providers = [dict(row) for row in results]
            return providers, None
            
    except Exception as e:
        return None, str(e)

async def get_all_provider_names() -> tuple:
    """Get a list of all provider names"""
    try:
        async with database.get_db_connection() as conn:
            table = 'providers_mock' if config.USE_MOCK_DATA else 'providers'
            
            query = f"""
                SELECT provider_name 
                FROM {config.DB_SCHEMA}.{table} 
                ORDER BY provider_name
            """
            results = await conn.fetch(query)
            
            if not results:
                return None, "No providers found in database"
            
            provider_names = [row['provider_name'] for row in results]
            return provider_names, None
            
    except Exception as e:
        return None, str(e)

async def match_providers_by_criteria(match_criteria: dict) -> tuple:
    """Match providers based on given criteria"""
    try:
        validated_data = validate_match_request(match_criteria)
        table = 'providers_mock' if config.USE_MOCK_DATA else 'providers'

        async with database.get_db_connection() as conn:
            matches = await find_matching_providers(
                conn,
                req=validated_data,
                table=table
            )
            
            return matches, None
            
    except InvalidUsage as e:
        return None, ("INVALID_REQUEST", str(e))
            
    except ProviderMatchError as e:
        return None, (e.error_code, e.message, e.details)
        
    except Exception as e:
        return None, ("SERVER_ERROR", str(e))

def setup_provider_routes(blueprint: Blueprint) -> None:
    """Setup provider routes on the given blueprint"""
    
    @blueprint.get("/providers")
    async def get_providers(request: Request) -> json:
        """Get all providers"""
        providers, error = await get_all_providers()
        
        if error:
            return error_response(
                message="Internal server error",
                error_code='SERVER_ERROR',
                details={'error': error},
                status=500
            )
            
        return success_response(
            data=providers,
            message=f"Found {len(providers)} providers"
        )

    @blueprint.post("/providers/match")
    async def match_providers(request: Request) -> json:
        """Match providers based on request criteria"""
        matches, error = await match_providers_by_criteria(request.json)
        
        if error:
            if isinstance(error, tuple):
                error_code, message, *details = error
                return error_response(
                    message=message,
                    error_code=error_code,
                    details=details[0] if details else {'error': message},
                    status=400 if error_code != 'SERVER_ERROR' else 500
                )
            return error_response(
                message="Internal server error",
                error_code='SERVER_ERROR',
                details={'error': str(error)},
                status=500
            )
                
        return success_response(
            data=matches,
            message=f"Found {len(matches)} matching providers"
        )

    @blueprint.get("/providers/id/<provider_id:int>")
    async def get_provider(request: Request, provider_id: int) -> json:
        """Get a specific provider by ID"""
        provider, error = await get_provider_by_id(provider_id)
        
        if error:
            if "not found" in error:
                return error_response(
                    message="Provider not found",
                    error_code='NOT_FOUND',
                    details={'error': error},
                    status=404
                )
            return error_response(
                message="Internal server error",
                error_code='SERVER_ERROR',
                details={'error': error},
                status=500
            )
            
        return success_response(
            data=provider,
            message=f"Provider {provider_id} retrieved successfully"
        )

    @blueprint.post("/providers/name")
    async def get_provider_by_name_route(request: Request) -> json:
        """Get providers that match the given name"""
        try:
            provider_name = request.json.get('name')
            if not provider_name:
                raise InvalidUsage("Name parameter is required")

            providers, error = await get_provider_info_by_name(provider_name)
            
            if error:
                if "No providers found" in error:
                    raise NotFound(error)
                raise Exception(error)
            
            return success_response(
                data=providers,
                message=f"Found {len(providers)} providers matching '{provider_name}'"
            )
                
        except InvalidUsage as e:
            return error_response(
                message="Invalid request",
                error_code='INVALID_REQUEST',
                details={'error': str(e)},
                status=400
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

    @blueprint.get("/providers/name_list")
    async def get_provider_names(request: Request) -> json:
        """Get a list of all provider names"""
        names, error = await get_all_provider_names()
        
        if error:
            if "No providers found" in error:
                return error_response(
                    message="No providers found",
                    error_code='NOT_FOUND',
                    details={'error': error},
                    status=404
                )
            return error_response(
                message="Internal server error",
                error_code='SERVER_ERROR',
                details={'error': error},
                status=500
            )
            
        return success_response(
            data=names,
            message=f"Found {len(names)} provider names"
        ) 