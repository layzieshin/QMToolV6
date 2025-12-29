"""Connection Information DTO."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ConnectionInfoDTO:
    """
    Data Transfer Object for database connection information.
    
    Attributes:
        database_url: SQLAlchemy connection URL
        engine_name: Name of the database engine (e.g., 'sqlite')
        database_path: Path to database file (for file-based DBs)
        is_connected: Whether connection is active
        pool_size: Current connection pool size
        active_connections: Number of active connections
    """
    database_url: str
    engine_name: str
    database_path: Optional[str] = None
    is_connected: bool = False
    pool_size: int = 0
    active_connections: int = 0
