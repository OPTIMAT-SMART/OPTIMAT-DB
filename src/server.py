"""
OPTIMAT Backend Server
-------------------
This module provides the main server implementation for the OPTIMAT Backend Server.
It handles provider matching requests based on environment configuration.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
import os

from sanic import Sanic, response
from sanic.request import Request
from sanic.response import JSONResponse
from sanic_cors import CORS

from src.services.provider_matcher import find_matching_providers, ProviderMatchError

# Server configuration
SERVER_CONFIG = {
    'host': os.getenv('SERVER_HOST', '0.0.0.0'),
    'port': int(os.getenv('SERVER_PORT', '8000')),
    'debug': os.getenv('DEBUG', 'false').lower() == 'true',
    'workers': int(os.getenv('WORKERS', '1'))
}

# Database configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

# Create the Sanic app
app = Sanic("optimat_backend")
app.config.KEEP_ALIVE_TIMEOUT = 600
app.config.RESPONSE_TIMEOUT = 600
app.config.REQUEST_TIMEOUT = 600
CORS(app)

# Initialize database pool
db_pool = None

@app.before_server_start
async def setup_db(app, loop):
    """Initialize database connection pool before server starts"""
    global db_pool
    app.config.USE_MOCK = True  # Always use mock database for now
    db_pool = SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        cursor_factory=RealDictCursor,
        **DB_CONFIG
    )

@app.before_server_stop
async def close_db(app, loop):
    """Close all database connections before server stops"""
    global db_pool
    if db_pool:
        db_pool.closeall()

def get_db():
    """Get a database connection from the pool"""
    return db_pool.getconn()

def release_db(conn):
    """Release a database connection back to the pool"""
    db_pool.putconn(conn)

def json_res(value: Any, status: int = 200) -> JSONResponse:
    """Create a JSON response with optional status code."""
    return response.json(value, status=status)

class APIError(Exception):
    """Base class for API errors"""
    def __init__(self, message: str, status_code: int = 400, error_code: str = 'INVALID_REQUEST'):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

class ValidationError(APIError):
    """Raised when request validation fails"""
    def __init__(self, message: str, field: Optional[str] = None):
        error_msg = f"Validation error for field '{field}': {message}" if field else message
        super().__init__(error_msg, 400, 'VALIDATION_ERROR')

class DatabaseError(APIError):
    """Raised when database operations fail"""
    def __init__(self, message: str):
        super().__init__(f"Database error: {message}", 500, 'DATABASE_ERROR')

def validate_provider_match_request(req_data: Dict) -> None:
    """Validate the provider matching request data."""
    if not req_data:
        raise ValidationError('Request body is empty or invalid JSON')
    
    required_fields = {
        'departureTime': 'Departure time',
        'returnTime': 'Return time',
        'originAddress': 'Origin address',
        'destinationAddress': 'Destination address',
        'eligibility': 'Eligibility criteria',
        'equipment': 'Equipment needs',
        'healthConditions': 'Health conditions',
        'needsCompanion': 'Companion requirement',
        'allowsSharing': 'Ride sharing preference'
    }
    
    # Check for missing fields
    missing_fields = [field for field in required_fields if field not in req_data]
    if missing_fields:
        field_names = [required_fields[f] for f in missing_fields]
        raise ValidationError(f"Missing required fields: {', '.join(field_names)}")
    
    # Validate date formats
    try:
        datetime.fromisoformat(req_data['departureTime'].replace('Z', '+00:00'))
        datetime.fromisoformat(req_data['returnTime'].replace('Z', '+00:00'))
    except ValueError as e:
        raise ValidationError("Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS+HH:MM)", "departureTime/returnTime")
    
    # Validate address fields are not empty
    if not req_data['originAddress'].strip():
        raise ValidationError("Origin address cannot be empty", "originAddress")
    if not req_data['destinationAddress'].strip():
        raise ValidationError("Destination address cannot be empty", "destinationAddress")
    
    # Validate lists
    if not isinstance(req_data['eligibility'], list):
        raise ValidationError("Eligibility must be a list", "eligibility")
    if not isinstance(req_data['equipment'], list):
        raise ValidationError("Equipment needs must be a list", "equipment")
    if not isinstance(req_data['healthConditions'], list):
        raise ValidationError("Health conditions must be a list", "healthConditions")
    
    # Validate boolean fields
    if not isinstance(req_data['needsCompanion'], bool):
        raise ValidationError("Companion requirement must be a boolean", "needsCompanion")
    if not isinstance(req_data['allowsSharing'], bool):
        raise ValidationError("Ride sharing preference must be a boolean", "allowsSharing")

@app.route('/api/match', methods=['POST'])
async def provider_match(request: Request) -> JSONResponse:
    """Handle provider matching requests based on user requirements."""
    conn = None
    try:
        # Validate request
        validate_provider_match_request(request.json)
        
        # Get database connection
        conn = get_db()
        cur = conn.cursor()
        
        try:
            # Find matching providers
            table = 'providers_mock' if request.app.config.USE_MOCK else 'providers'
            result = find_matching_providers(cur, request.json, table=table)
            return json_res({
                'status': 'SUCCESS',
                'data': result,
                'message': f"Found {len(result)} matching providers"
            })
            
        except ProviderMatchError as e:
            # Handle specific provider matching errors
            return json_res({
                'status': 'MATCH_ERROR',
                'error': str(e),
                'error_code': e.error_code,
                'details': e.details
            }, 400)
            
        except psycopg2.Error as e:
            # Handle database errors
            raise DatabaseError(f"Database query failed: {e.pgerror}")
    
    except ValidationError as e:
        # Handle validation errors
        return json_res({
            'status': e.error_code,
            'error': e.message,
            'field': getattr(e, 'field', None)
        }, e.status_code)
        
    except DatabaseError as e:
        # Handle database errors
        return json_res({
            'status': e.error_code,
            'error': e.message
        }, e.status_code)
        
    except Exception as e:
        # Handle unexpected errors
        return json_res({
            'status': 'SERVER_ERROR',
            'error': str(e),
            'error_code': 'UNEXPECTED_ERROR'
        }, 500)
    
    finally:
        if conn:
            release_db(conn)

if __name__ == '__main__':
    app.run(
        host=SERVER_CONFIG['host'],
        port=SERVER_CONFIG['port'],
        workers=SERVER_CONFIG['workers'],
        debug=SERVER_CONFIG['debug']
    )
