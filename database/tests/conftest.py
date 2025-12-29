"""Test fixtures for database tests."""
import pytest
from sqlalchemy import Column, Integer, String

from database.logic.services.database_service import DatabaseService
from database.models.base import Base


# Test entity for repository tests
class SampleEntity(Base):
    """Sample entity for testing BaseRepository."""
    __tablename__ = "test_entities"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)


@pytest.fixture
def database_service():
    """Create an in-memory database service for testing."""
    service = DatabaseService("sqlite:///:memory:", echo=False)
    service.ensure_schema()
    yield service
    service.close()


@pytest.fixture
def db_session(database_service):
    """Get a database session for testing."""
    return database_service.get_session()
