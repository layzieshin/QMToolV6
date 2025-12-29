"""Tests for SchemaRegistry."""
import pytest

from database.logic.services.schema_registry import SchemaRegistry
from database.models.base import Base


class TestSchemaRegistry:
    """Tests for SchemaRegistry."""
    
    @pytest.fixture
    def schema_registry(self, database_service):
        """Get schema registry from database service."""
        return database_service.get_schema_registry()
    
    def test_initialization(self, schema_registry):
        """Test schema registry initialization."""
        # Assert
        assert schema_registry is not None
    
    def test_ensure_schema(self, database_service):
        """Test ensuring schema is created."""
        # Arrange
        service = database_service
        registry = service.get_schema_registry()
        
        # Act
        registry.ensure_schema()
        
        # Assert
        assert registry.validate_schema()
    
    def test_validate_schema(self, schema_registry):
        """Test schema validation."""
        # Act
        schema_registry.ensure_schema()
        is_valid = schema_registry.validate_schema()
        
        # Assert
        assert is_valid is True
    
    def test_get_table_names(self, schema_registry):
        """Test getting table names."""
        # Arrange
        schema_registry.ensure_schema()
        
        # Act
        tables = schema_registry.get_table_names()
        
        # Assert
        assert isinstance(tables, list)
        # Should have at least test_entities table
        assert "test_entities" in tables
    
    def test_get_model_count(self, schema_registry):
        """Test getting model count."""
        # Act
        count = schema_registry.get_model_count()
        
        # Assert
        assert count >= 1  # At least TestEntity
    
    def test_drop_all_tables(self, database_service):
        """Test dropping all tables."""
        # Arrange
        registry = database_service.get_schema_registry()
        registry.ensure_schema()
        
        # Act
        registry.drop_all_tables()
        
        # Assert
        tables = registry.get_table_names()
        assert len(tables) == 0
        
        # Recreate for other tests
        registry.ensure_schema()
