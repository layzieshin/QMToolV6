"""Database Engine Enumeration."""
from enum import Enum


class DbEngineEnum(Enum):
    """
    Supported database engine types.
    
    Currently focused on SQLite for MVP.
    Future versions may support PostgreSQL, MySQL, etc.
    """
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MEMORY = "memory"  # SQLite in-memory for testing
