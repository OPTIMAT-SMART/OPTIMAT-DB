"""
API Routes
----------
Collection of all API routes and blueprints.
"""
from sanic.request import Request
from sanic import Blueprint
from src.routes.provider_routes import setup_provider_routes
from src.routes.util_routes import setup_util_routes
from src.routes.chat_routes import setup_chat_routes
import json 
from utils.responses import success_response, error_response

# Create API blueprint
api_v1 = Blueprint('api_v1', url_prefix='')

# Health check route
@api_v1.get("/health")
async def chat_health_check(request: Request) -> json:
    """Health check endpoint for the chat service"""
    try:
        return success_response(
            data={"status": "healthy"},
            message="Chat service is healthy"
        )
    except Exception as e:
        return error_response(
            message="Chat service health check failed",
            error_code="HEALTH_CHECK_FAILED", 
            details={"error": str(e)},
            status=500
        )

# Initialize routes
setup_provider_routes(api_v1)
setup_util_routes(api_v1)
setup_chat_routes(api_v1)