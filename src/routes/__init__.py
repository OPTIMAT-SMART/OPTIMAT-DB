"""
API Routes
----------
Collection of all API routes and blueprints.
"""

from sanic import Blueprint
from src.routes.provider_routes import setup_provider_routes
from src.routes.util_routes import setup_util_routes
from src.routes.chat_routes import setup_chat_routes

# Create API blueprint
api_v1 = Blueprint('api_v1', url_prefix='/api/v1')

# Initialize routes
setup_provider_routes(api_v1)
setup_util_routes(api_v1)
setup_chat_routes(api_v1)