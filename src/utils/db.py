# src/utils/db.py
"""
Database Utilities
------------------
Handles database connections and pooling.
"""

import asyncpg
import logging
from contextlib import asynccontextmanager
from src.utils.config import config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None

    async def init_pool(self):
        """Initialize the asyncpg connection pool optimized for high scale."""
        try:
            self.pool = await asyncpg.create_pool(
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME,
                host=config.DB_HOST,
                port=config.DB_PORT,
                min_size=10,
                max_size=100,
                command_timeout=30,
                max_inactive_connection_lifetime=300.0,
                statement_cache_size=0  # Disable statement caching
            )
            logger.info("Database pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    @asynccontextmanager
    async def get_db_connection(self):
        """
        Provide a transactional scope around a series of operations.
        """
        if not self.pool:
            raise Exception("Database pool is not initialized. Call init_pool() first.")
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.release(conn)

    async def close(self):
        """Close the database pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

database = Database()