"""
Configuration Management
----------------------
Handles all configuration settings for the application using environment variables
and Pydantic for type safety and validation.
"""

import os
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional




class Config(BaseSettings):
    """Combined configuration"""

    # Server settings
    SERVER_HOST: str = Field(default='0.0.0.0', env='SERVER_HOST')
    SERVER_PORT: int = Field(default=8000, env='SERVER_PORT')
    SERVER_WORKERS: int = Field(default=1, env='SERVER_WORKERS')
    SERVER_DEBUG: bool = Field(default=False, env='SERVER_DEBUG')
    USE_MOCK_DATA: bool = Field(default=False, env='USE_MOCK_DATA')

    # Database configuration
    DB_HOST: str = Field(default='localhost', env='DB_HOST')
    DB_PORT: int = Field(default=5432, env='DB_PORT')
    DB_NAME: str = Field(default='optimat', env='DB_NAME')
    DB_USER: str = Field(default='postgres', env='DB_USER')
    DB_PASSWORD: str = Field(default='', env='DB_PASSWORD')
    DB_SCHEMA: str = Field(default='atccc', env='DB_SCHEMA')

    # Logging configuration
    LOG_LEVEL: str = Field(default='INFO', env='LOG_LEVEL')
    LOG_FORMAT: str = Field(default='%(asctime)s - %(name)s - %(levelname)s - %(message)s', env='LOG_FORMAT')
    LOG_FILE: Optional[str] = Field(default=None, env='LOG_FILE')

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "forbid"  # Disallow extra fields not defined above


# Instantiate the configuration
config = Config() 