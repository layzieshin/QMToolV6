"""Tests for BaseRepository."""
import pytest

from database.logic.repository.base_repository import BaseRepository
from database.logic.exceptions.database_exception import RepositoryException
from database.tests.conftest import SampleEntity


class TestBaseRepository:
    """Tests for BaseRepository."""
    
    @pytest.fixture
    def repository(self, db_session):
        """Create a test repository."""
        return BaseRepository(SampleEntity, db_session)
    
    def test_initialization(self, repository):
        """Test repository initialization."""
        # Assert
        assert repository is not None
        assert repository.entity_class == SampleEntity
    
    def test_create(self, repository):
        """Test creating an entity."""
        # Arrange
        entity = SampleEntity(name="Test Create", description="Test description")
        
        # Act
        result = repository.create(entity)
        
        # Assert
        assert result is not None
        assert result.id is not None
        assert result.name == "Test Create"
    
    def test_get_by_id(self, repository):
        """Test getting entity by ID."""
        # Arrange
        entity = SampleEntity(name="Test Get", description="Test get by id")
        created = repository.create(entity)
        
        # Act
        result = repository.get_by_id(created.id)
        
        # Assert
        assert result is not None
        assert result.id == created.id
        assert result.name == "Test Get"
    
    def test_get_by_id_not_found(self, repository):
        """Test getting non-existent entity."""
        # Act
        result = repository.get_by_id(999999)
        
        # Assert
        assert result is None
    
    def test_get_all(self, repository):
        """Test getting all entities."""
        # Arrange
        entity1 = SampleEntity(name="Entity 1", description="First")
        entity2 = SampleEntity(name="Entity 2", description="Second")
        repository.create(entity1)
        repository.create(entity2)
        
        # Act
        results = repository.get_all()
        
        # Assert
        assert len(results) >= 2
    
    def test_get_all_with_limit(self, repository):
        """Test getting entities with limit."""
        # Arrange
        for i in range(5):
            entity = SampleEntity(name=f"Entity {i}", description=f"Description {i}")
            repository.create(entity)
        
        # Act
        results = repository.get_all(limit=3)
        
        # Assert
        assert len(results) == 3
    
    def test_get_all_with_offset(self, repository):
        """Test getting entities with offset."""
        # Arrange
        entities = []
        for i in range(5):
            entity = SampleEntity(name=f"Entity {i}", description=f"Description {i}")
            created = repository.create(entity)
            entities.append(created)
        
        # Act
        results = repository.get_all(offset=2, limit=2)
        
        # Assert
        assert len(results) == 2
    
    def test_update(self, repository):
        """Test updating an entity."""
        # Arrange
        entity = SampleEntity(name="Original", description="Original description")
        created = repository.create(entity)
        
        # Act
        created.name = "Updated"
        created.description = "Updated description"
        updated = repository.update(created)
        
        # Assert
        assert updated.name == "Updated"
        assert updated.description == "Updated description"
        
        # Verify in database
        result = repository.get_by_id(created.id)
        assert result.name == "Updated"
    
    def test_delete(self, repository):
        """Test deleting an entity."""
        # Arrange
        entity = SampleEntity(name="To Delete", description="Will be deleted")
        created = repository.create(entity)
        entity_id = created.id
        
        # Act
        repository.delete(created)
        
        # Assert
        result = repository.get_by_id(entity_id)
        assert result is None
    
    def test_delete_by_id(self, repository):
        """Test deleting entity by ID."""
        # Arrange
        entity = SampleEntity(name="Delete by ID", description="Delete test")
        created = repository.create(entity)
        entity_id = created.id
        
        # Act
        result = repository.delete_by_id(entity_id)
        
        # Assert
        assert result is True
        assert repository.get_by_id(entity_id) is None
    
    def test_delete_by_id_not_found(self, repository):
        """Test deleting non-existent entity."""
        # Act
        result = repository.delete_by_id(999999)
        
        # Assert
        assert result is False
    
    def test_count(self, repository):
        """Test counting entities."""
        # Arrange
        initial_count = repository.count()
        entity1 = SampleEntity(name="Count 1", description="First")
        entity2 = SampleEntity(name="Count 2", description="Second")
        repository.create(entity1)
        repository.create(entity2)
        
        # Act
        count = repository.count()
        
        # Assert
        assert count == initial_count + 2
    
    def test_exists(self, repository):
        """Test checking if entity exists."""
        # Arrange
        entity = SampleEntity(name="Exists Test", description="Existence check")
        created = repository.create(entity)
        
        # Act
        exists = repository.exists(created.id)
        not_exists = repository.exists(999999)
        
        # Assert
        assert exists is True
        assert not_exists is False
