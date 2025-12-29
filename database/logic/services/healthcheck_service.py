"""Health check service for database monitoring."""
from dataclasses import dataclass
from typing import Optional
import time

from sqlalchemy import text

from .database_service_interface import DatabaseServiceInterface
from ..exceptions.database_exception import DatabaseException


@dataclass
class HealthCheckResult:
    """
    Result of a health check.
    
    Attributes:
        is_healthy: Whether database is healthy
        response_time_ms: Response time in milliseconds
        error_message: Error message if unhealthy
        connection_count: Number of active connections
    """
    is_healthy: bool
    response_time_ms: float
    error_message: Optional[str] = None
    connection_count: int = 0


class HealthcheckService:
    """
    Service for monitoring database health.
    
    Provides health checks and diagnostics for the database.
    """
    
    def __init__(self, database_service: DatabaseServiceInterface):
        """
        Initialize HealthcheckService.
        
        Args:
            database_service: Database service to monitor
        """
        self._database_service = database_service
    
    def check_health(self) -> HealthCheckResult:
        """
        Perform a health check on the database.
        
        Returns:
            HealthCheckResult: Result of the health check
        """
        start_time = time.time()
        
        try:
            # Get a session and execute a simple query
            session = self._database_service.get_session()
            session.execute(text("SELECT 1"))
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Get connection info
            conn_info = self._database_service.get_connection_info()
            
            return HealthCheckResult(
                is_healthy=True,
                response_time_ms=response_time_ms,
                connection_count=conn_info.active_connections
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                is_healthy=False,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )
    
    def ping(self) -> bool:
        """
        Quick ping to check if database is accessible.
        
        Returns:
            bool: True if database is accessible, False otherwise
        """
        try:
            session = self._database_service.get_session()
            session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
    
    def get_connection_info(self) -> dict:
        """
        Get detailed connection information.
        
        Returns:
            dict: Connection information
        """
        try:
            conn_info = self._database_service.get_connection_info()
            return {
                "database_url": conn_info.database_url,
                "engine_name": conn_info.engine_name,
                "database_path": conn_info.database_path,
                "is_connected": conn_info.is_connected,
                "pool_size": conn_info.pool_size,
                "active_connections": conn_info.active_connections
            }
        except Exception as e:
            return {
                "error": str(e)
            }
