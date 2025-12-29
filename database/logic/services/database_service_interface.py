"""Interface for DatabaseService."""
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Optional
import sqlite3

from sqlalchemy.orm import Session

from ..dto.connection_info_dto import ConnectionInfoDTO


class UnitOfWorkInterface(ABC):
    """Interface for Unit of Work pattern."""
    
    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
    
    @abstractmethod
    def get_session(self) -> Session:
        """Get the SQLAlchemy session for this Unit of Work."""
        pass


class DatabaseServiceInterface(ABC):
    """
    Interface for database service.
    
    Defines the contract for database access across the application.
    Features should depend on this interface, not concrete implementations.
    """
    
    @abstractmethod
    def get_session(self) -> Session:
        """
        Get thread-local SQLAlchemy session.
        
        Returns:
            Session: Thread-local database session
            
        Raises:
            SessionException: If session cannot be created
        """
        pass
    
    @abstractmethod
    def get_connection(self) -> sqlite3.Connection:
        """
        Get thread-local raw SQLite connection for legacy code.
        
        Returns:
            sqlite3.Connection: Thread-local raw database connection
            
        Raises:
            ConnectionException: If connection cannot be created
        """
        pass
    
    @abstractmethod
    def unit_of_work(self) -> AbstractContextManager[UnitOfWorkInterface]:
        """
        Create a Unit of Work context for transactional operations.
        
        Usage:
            with database_service.unit_of_work() as uow:
                # Perform operations
                uow.commit()  # Or let context manager auto-commit
        
        Returns:
            Context manager for Unit of Work
            
        Raises:
            UnitOfWorkException: If UoW cannot be created
        """
        pass
    
    @abstractmethod
    def get_connection_info(self) -> ConnectionInfoDTO:
        """
        Get current connection information.
        
        Returns:
            ConnectionInfoDTO: Current connection details
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """
        Close all database connections and sessions.
        
        Should be called on application shutdown.
        """
        pass
    
    @abstractmethod
    def ensure_schema(self) -> None:
        """
        Ensure database schema is created.
        
        Creates all tables defined in models if they don't exist.
        
        Raises:
            SchemaException: If schema creation fails
        """
        pass
