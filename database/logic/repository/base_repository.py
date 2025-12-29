"""Base Repository with common CRUD operations."""
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..exceptions.database_exception import RepositoryException

# Generic type for entity class
T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository providing common CRUD operations.
    
    All feature-specific repositories should extend this class.
    
    Type parameter T represents the entity type (e.g., UserEntity).
    
    Usage:
        class UserRepository(BaseRepository[UserEntity]):
            def __init__(self, session: Session):
                super().__init__(UserEntity, session)
            
            # Add custom query methods here
            def get_by_username(self, username: str) -> Optional[UserEntity]:
                return self._session.query(self.entity_class).filter_by(username=username).first()
    """
    
    def __init__(self, entity_class: Type[T], session: Session):
        """
        Initialize repository.
        
        Args:
            entity_class: The SQLAlchemy entity class
            session: SQLAlchemy session to use for queries
        """
        self.entity_class = entity_class
        self._session = session
    
    def create(self, entity: T) -> T:
        """
        Create a new entity.
        
        Args:
            entity: Entity instance to create
            
        Returns:
            T: Created entity (with ID assigned)
            
        Raises:
            RepositoryException: If creation fails
        """
        try:
            self._session.add(entity)
            self._session.flush()  # Flush to get ID without committing
            return entity
        except Exception as e:
            raise RepositoryException(
                f"Failed to create {self.entity_class.__name__}: {str(e)}",
                cause=e
            )
    
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Primary key value
            
        Returns:
            Optional[T]: Entity if found, None otherwise
            
        Raises:
            RepositoryException: If query fails
        """
        try:
            return self._session.get(self.entity_class, entity_id)
        except Exception as e:
            raise RepositoryException(
                f"Failed to get {self.entity_class.__name__} by ID {entity_id}: {str(e)}",
                cause=e
            )
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """
        Get all entities.
        
        Args:
            limit: Maximum number of results (None for no limit)
            offset: Number of results to skip
            
        Returns:
            List[T]: List of entities
            
        Raises:
            RepositoryException: If query fails
        """
        try:
            query = select(self.entity_class)
            
            if offset > 0:
                query = query.offset(offset)
            
            if limit is not None:
                query = query.limit(limit)
            
            result = self._session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            raise RepositoryException(
                f"Failed to get all {self.entity_class.__name__}: {str(e)}",
                cause=e
            )
    
    def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: Entity instance to update
            
        Returns:
            T: Updated entity
            
        Raises:
            RepositoryException: If update fails
        """
        try:
            self._session.merge(entity)
            self._session.flush()
            return entity
        except Exception as e:
            raise RepositoryException(
                f"Failed to update {self.entity_class.__name__}: {str(e)}",
                cause=e
            )
    
    def delete(self, entity: T) -> None:
        """
        Delete an entity.
        
        Args:
            entity: Entity instance to delete
            
        Raises:
            RepositoryException: If deletion fails
        """
        try:
            self._session.delete(entity)
            self._session.flush()
        except Exception as e:
            raise RepositoryException(
                f"Failed to delete {self.entity_class.__name__}: {str(e)}",
                cause=e
            )
    
    def delete_by_id(self, entity_id: int) -> bool:
        """
        Delete entity by ID.
        
        Args:
            entity_id: Primary key value
            
        Returns:
            bool: True if entity was deleted, False if not found
            
        Raises:
            RepositoryException: If deletion fails
        """
        try:
            entity = self.get_by_id(entity_id)
            if entity is None:
                return False
            
            self.delete(entity)
            return True
        except Exception as e:
            raise RepositoryException(
                f"Failed to delete {self.entity_class.__name__} by ID {entity_id}: {str(e)}",
                cause=e
            )
    
    def count(self) -> int:
        """
        Count total number of entities.
        
        Returns:
            int: Total count
            
        Raises:
            RepositoryException: If count fails
        """
        try:
            query = select(self.entity_class)
            result = self._session.execute(query)
            return len(list(result.scalars().all()))
        except Exception as e:
            raise RepositoryException(
                f"Failed to count {self.entity_class.__name__}: {str(e)}",
                cause=e
            )
    
    def exists(self, entity_id: int) -> bool:
        """
        Check if entity exists.
        
        Args:
            entity_id: Primary key value
            
        Returns:
            bool: True if entity exists, False otherwise
        """
        return self.get_by_id(entity_id) is not None
