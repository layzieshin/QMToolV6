"""DatabaseService implementation with SQLAlchemy 2.0 and thread-local sessions."""
import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional
from pathlib import Path

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from .database_service_interface import DatabaseServiceInterface, UnitOfWorkInterface
from .unit_of_work import UnitOfWork
from .schema_registry import SchemaRegistry
from ..dto.connection_info_dto import ConnectionInfoDTO
from ..enum.db_engine_enum import DbEngineEnum
from ..exceptions.database_exception import ConnectionException, SessionException, SchemaException
from ..exceptions.transaction_exception import UnitOfWorkException
from ...models.base import Base


class DatabaseService(DatabaseServiceInterface):
    """
    Database service implementation with SQLite support.
    
    Features:
    - Thread-local sessions via scoped_session
    - Unit-of-Work pattern for transactions
    - Legacy sqlite3.Connection access
    - Automatic schema creation
    - Thread-safe operations
    """
    
    def __init__(self, database_url: str = "sqlite:///qmtool.db", echo: bool = False):
        """
        Initialize DatabaseService.
        
        Args:
            database_url: SQLAlchemy database URL (default: sqlite:///qmtool.db)
            echo: Whether to echo SQL statements (default: False)
        """
        self._database_url = database_url
        self._echo = echo
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._scoped_session: Optional[scoped_session] = None
        self._schema_registry: Optional[SchemaRegistry] = None
        
        # Thread-local storage for raw SQLite connections
        self._local = threading.local()
        
        # Initialize database
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize database engine and session factory."""
        try:
            # Create engine
            self._engine = create_engine(
                self._database_url,
                echo=self._echo,
                # SQLite-specific settings for better concurrency
                connect_args={"check_same_thread": False} if self._database_url.startswith("sqlite") else {}
            )
            
            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            # Create scoped session for thread-local sessions
            self._scoped_session = scoped_session(self._session_factory)
            
            # Create schema registry
            self._schema_registry = SchemaRegistry(self._engine, Base)
            
        except Exception as e:
            raise ConnectionException(
                f"Failed to initialize database: {str(e)}",
                cause=e
            )
    
    def get_session(self) -> Session:
        """
        Get thread-local SQLAlchemy session.
        
        Returns:
            Session: Thread-local database session
            
        Raises:
            SessionException: If session cannot be created
        """
        try:
            if self._scoped_session is None:
                raise SessionException("Database not initialized")
            
            return self._scoped_session()
        except Exception as e:
            raise SessionException(
                f"Failed to get session: {str(e)}",
                cause=e
            )
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get thread-local raw SQLite connection for legacy code.
        
        Returns:
            sqlite3.Connection: Thread-local raw database connection
            
        Raises:
            ConnectionException: If connection cannot be created
        """
        # Check if this thread already has a connection
        if hasattr(self._local, 'connection') and self._local.connection is not None:
            return self._local.connection
        
        try:
            # Extract database path from URL
            if self._database_url.startswith("sqlite:///"):
                db_path = self._database_url.replace("sqlite:///", "")
            elif self._database_url == "sqlite:///:memory:":
                db_path = ":memory:"
            else:
                raise ConnectionException(
                    "get_connection() only supports SQLite databases"
                )
            
            # Create thread-local connection
            self._local.connection = sqlite3.connect(
                db_path,
                check_same_thread=False
            )
            
            return self._local.connection
            
        except Exception as e:
            raise ConnectionException(
                f"Failed to create raw connection: {str(e)}",
                cause=e
            )
    
    @contextmanager
    def unit_of_work(self) -> UnitOfWorkInterface:
        """
        Create a Unit of Work context for transactional operations.
        
        Usage:
            with database_service.unit_of_work() as uow:
                # Perform operations
                # Auto-commits on successful exit
        
        Yields:
            UnitOfWork: Unit of Work instance
            
        Raises:
            UnitOfWorkException: If UoW cannot be created
        """
        session = None
        try:
            session = self.get_session()
            with UnitOfWork(session, auto_commit=True) as uow:
                yield uow
        except Exception as e:
            if session is not None:
                try:
                    session.rollback()
                except Exception:
                    pass
            raise UnitOfWorkException(
                f"Unit of Work failed: {str(e)}",
                cause=e
            )
    
    def get_connection_info(self) -> ConnectionInfoDTO:
        """
        Get current connection information.
        
        Returns:
            ConnectionInfoDTO: Current connection details
        """
        engine_name = DbEngineEnum.SQLITE.value
        database_path = None
        is_connected = self._engine is not None
        
        if self._database_url.startswith("sqlite:///"):
            database_path = self._database_url.replace("sqlite:///", "")
        elif self._database_url == "sqlite:///:memory:":
            engine_name = DbEngineEnum.MEMORY.value
            database_path = ":memory:"
        
        # Get pool stats if available
        pool_size = 0
        active_connections = 0
        
        if self._engine is not None and hasattr(self._engine.pool, 'size'):
            try:
                pool_size = self._engine.pool.size()
                active_connections = self._engine.pool.checkedout()
            except Exception:
                pass
        
        return ConnectionInfoDTO(
            database_url=self._database_url,
            engine_name=engine_name,
            database_path=database_path,
            is_connected=is_connected,
            pool_size=pool_size,
            active_connections=active_connections
        )
    
    def close(self) -> None:
        """
        Close all database connections and sessions.
        
        Should be called on application shutdown.
        """
        try:
            # Close scoped sessions
            if self._scoped_session is not None:
                self._scoped_session.remove()
            
            # Close raw connections (thread-local)
            if hasattr(self._local, 'connection') and self._local.connection is not None:
                self._local.connection.close()
                self._local.connection = None
            
            # Dispose engine
            if self._engine is not None:
                self._engine.dispose()
                
        except Exception:
            # Ignore errors during cleanup
            pass
    
    def ensure_schema(self) -> None:
        """
        Ensure database schema is created.
        
        Creates all tables defined in models if they don't exist.
        
        Raises:
            SchemaException: If schema creation fails
        """
        try:
            if self._schema_registry is None:
                raise SchemaException("Schema registry not initialized")
            
            self._schema_registry.ensure_schema()
        except Exception as e:
            raise SchemaException(
                f"Failed to ensure schema: {str(e)}",
                cause=e
            )
    
    def get_engine(self) -> Engine:
        """
        Get the SQLAlchemy engine.
        
        Returns:
            Engine: SQLAlchemy engine
        """
        if self._engine is None:
            raise ConnectionException("Database not initialized")
        return self._engine
    
    def get_schema_registry(self) -> SchemaRegistry:
        """
        Get the schema registry.
        
        Returns:
            SchemaRegistry: Schema registry instance
        """
        if self._schema_registry is None:
            raise SchemaException("Schema registry not initialized")
        return self._schema_registry
