"""
OPTIMAT Backend Server
---------------------
Main entry point for running the OPTIMAT Backend Server.
"""

from src.app import app  # Import the Sanic app
from src.utils.config import config

if __name__ == '__main__':
    app.run(
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        workers=config.SERVER_WORKERS,
        debug=config.SERVER_DEBUG
    )
