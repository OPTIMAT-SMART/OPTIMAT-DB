from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from utils.config import config
import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)

# Create the SQLAlchemy base class
Base = declarative_base()

# Create async engine using config values with connection pooling settings
DATABASE_URL = (
    f"postgresql+asyncpg://{config.DB_USER}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=config.SERVER_DEBUG,
    future=True,
    connect_args={
        "statement_cache_size": 0,  # Disable statement cache for PgBouncer compatibility
    }
)

# Create async session factory
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

@asynccontextmanager
async def get_session() -> AsyncSession:
    """
    Provide an asynchronous session for DB operations.
    Usage:
        async with get_session() as session:
            # perform DB operations
    """
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Session rollback because of exception: {e}")
            raise
        finally:
            await session.close()