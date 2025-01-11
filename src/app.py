"""
Sanic Application Initialization
--------------------------------
Creates and configures the Sanic app with all blueprints and settings.
"""

from sanic import Sanic
from sanic_cors import CORS
import logging
from src.utils.config import config
from src.routes import api_v1
from src.utils.db import database

# Set up logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT,
    filename=config.LOG_FILE
)
logger = logging.getLogger(__name__)

# Create the Sanic app instance
app = Sanic("optimat_backend")

# Configure the app settings
app.config.update({
    'KEEP_ALIVE_TIMEOUT': 600,
    'RESPONSE_TIMEOUT': 600,
    'REQUEST_TIMEOUT': 600,
    'USE_MOCK_DATA': config.USE_MOCK_DATA,
})

# Enable CORS
CORS(app)

# Register API routes
app.blueprint(api_v1)

@app.listener('before_server_start')
async def verify_db_connection(app, loop):
    """Verify database connection before server starts"""
    try:
        await database.init_pool()
        async with database.get_db_connection() as conn:
            version = await conn.fetchval('SELECT version()')
            logger.info(f"Connected to PostgreSQL: {version}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

@app.listener('after_server_stop')
async def cleanup_db(app, loop):
    """Close database pool after server stops"""
    await database.close()

if __name__ == "__main__":
    app.run(
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        debug=config.SERVER_DEBUG,
        workers=config.SERVER_WORKERS
    )