"""Tests for DatabaseService."""
import pytest
import sqlite3

from database.logic.services.database_service import DatabaseService
from database.logic.exceptions.database_exception import SessionException, SchemaException
from database.logic.exceptions.transaction_exception import UnitOfWorkException


class TestDatabaseService:
    """Tests for DatabaseService."""
    
    def test_initialization(self):
        """Test database service initialization."""
        # Arrange & Act
        service = DatabaseService("sqlite:///:memory:")
        
        # Assert
        assert service is not None
        assert service.get_connection_info().is_connected
        
        # Cleanup
        service.close()
    
    def test_get_session(self, database_service):
        """Test getting a session."""
        # Act
        session = database_service.get_session()
        
        # Assert
        assert session is not None
    
    def test_get_session_is_thread_local(self, database_service):
        """Test that sessions are thread-local."""
        # Act
        session1 = database_service.get_session()
        session2 = database_service.get_session()
        
        # Assert - same thread gets same session
        assert session1 is session2
    
    def test_get_connection(self, database_service):
        """Test getting a raw SQLite connection."""
        # Act
        conn = database_service.get_connection()
        
        # Assert
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        
        # Test connection works
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result == (1,)
    
    def test_get_connection_is_thread_local(self, database_service):
        """Test that connections are thread-local."""
        # Act
        conn1 = database_service.get_connection()
        conn2 = database_service.get_connection()
        
        # Assert - same thread gets same connection
        assert conn1 is conn2
    
    def test_unit_of_work_context(self, database_service):
        """Test Unit of Work context manager."""
        # Act & Assert
        with database_service.unit_of_work() as uow:
            assert uow is not None
            assert uow.get_session() is not None
    
    def test_unit_of_work_auto_commit(self, database_service):
        """Test Unit of Work auto-commits on success."""
        from database.tests.conftest import SampleEntity
        from sqlalchemy import select
        
        # Act
        with database_service.unit_of_work() as uow:
            session = uow.get_session()
            entity = SampleEntity(name="Test", description="Auto commit test")
            session.add(entity)
        
        # Assert - entity should be committed
        # Close the session and get a fresh one to verify commit
        database_service._scoped_session.remove()
        new_session = database_service.get_session()
        stmt = select(SampleEntity).where(SampleEntity.name == "Test")
        result = new_session.execute(stmt).scalar_one_or_none()
        assert result is not None
        assert result.description == "Auto commit test"
    
    def test_unit_of_work_rollback_on_exception(self, database_service):
        """Test Unit of Work rolls back on exception."""
        from database.tests.conftest import SampleEntity
        from database.logic.exceptions.transaction_exception import UnitOfWorkException
        from sqlalchemy import select
        
        # Act & Assert
        with pytest.raises(UnitOfWorkException):
            with database_service.unit_of_work() as uow:
                session = uow.get_session()
                entity = SampleEntity(name="Rollback", description="Should rollback")
                session.add(entity)
                raise ValueError("Simulated error")
        
        # Assert - entity should NOT be in database
        new_session = database_service.get_session()
        stmt = select(SampleEntity).where(SampleEntity.name == "Rollback")
        result = new_session.execute(stmt).scalar_one_or_none()
        assert result is None
    
    def test_get_connection_info(self, database_service):
        """Test getting connection information."""
        # Act
        info = database_service.get_connection_info()
        
        # Assert
        assert info is not None
        assert info.database_url == "sqlite:///:memory:"
        # In-memory databases have engine_name as "memory" or "sqlite"
        assert info.engine_name in ["memory", "sqlite"]
        assert info.is_connected is True
    
    def test_ensure_schema(self, database_service):
        """Test schema creation."""
        # Act
        database_service.ensure_schema()
        
        # Assert - verify schema registry
        schema_registry = database_service.get_schema_registry()
        assert schema_registry.validate_schema()
    
    def test_close(self):
        """Test closing database connections."""
        # Arrange
        service = DatabaseService("sqlite:///:memory:")
        service.get_session()  # Initialize session
        
        # Act
        service.close()
        
        # Assert - should be able to create new service
        new_service = DatabaseService("sqlite:///:memory:")
        assert new_service is not None
        new_service.close()
