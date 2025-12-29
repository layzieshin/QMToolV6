"""
Example: How to use the Database Feature in other features.

This demonstrates the dependency injection pattern and Unit-of-Work usage.
"""

from sqlalchemy import Column, Integer, String
from database.logic.services.database_service import DatabaseService
from database.logic.repository.base_repository import BaseRepository
from database.models.base import Base


# Step 1: Define your ORM Entity
class ExampleEntity(Base):
    """Example entity inheriting from database Base."""
    __tablename__ = "examples"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    value = Column(String(255), nullable=True)


# Step 2: Create a Repository (extends BaseRepository)
class ExampleRepository(BaseRepository[ExampleEntity]):
    """Repository for example entities."""
    
    def __init__(self, session):
        super().__init__(ExampleEntity, session)
    
    # Add custom query methods
    def get_by_name(self, name: str):
        """Get entity by name."""
        return self._session.query(ExampleEntity).filter_by(name=name).first()


# Step 3: Create a Service that uses DatabaseService
class ExampleService:
    """Example service using database via dependency injection."""
    
    def __init__(self, database_service):
        """
        Initialize service with database_service dependency.
        
        Args:
            database_service: DatabaseService instance (injected)
        """
        self._database_service = database_service
    
    def create_example(self, name: str, value: str) -> dict:
        """
        Create an example using Unit-of-Work pattern.
        
        Args:
            name: Example name
            value: Example value
            
        Returns:
            dict: Created example as dictionary
        """
        # Use Unit-of-Work for transactional boundary
        with self._database_service.unit_of_work() as uow:
            # Get repository from session
            session = uow.get_session()
            repo = ExampleRepository(session)
            
            # Create entity
            entity = ExampleEntity(name=name, value=value)
            created = repo.create(entity)
            
            # Auto-commits on successful exit
            return {
                "id": created.id,
                "name": created.name,
                "value": created.value
            }
    
    def get_example(self, example_id: int) -> dict:
        """
        Get an example by ID.
        
        Args:
            example_id: Example ID
            
        Returns:
            dict: Example data or None
        """
        # For read-only operations, can use get_session directly
        session = self._database_service.get_session()
        repo = ExampleRepository(session)
        
        entity = repo.get_by_id(example_id)
        if entity is None:
            return None
        
        return {
            "id": entity.id,
            "name": entity.name,
            "value": entity.value
        }
    
    def update_example(self, example_id: int, new_value: str) -> dict:
        """
        Update an example using Unit-of-Work.
        
        Args:
            example_id: Example ID
            new_value: New value
            
        Returns:
            dict: Updated example
        """
        with self._database_service.unit_of_work() as uow:
            session = uow.get_session()
            repo = ExampleRepository(session)
            
            # Get and update
            entity = repo.get_by_id(example_id)
            if entity is None:
                raise ValueError(f"Example {example_id} not found")
            
            entity.value = new_value
            updated = repo.update(entity)
            
            # Auto-commits
            return {
                "id": updated.id,
                "name": updated.name,
                "value": updated.value
            }


# Example usage
if __name__ == "__main__":
    # Initialize database service
    db_service = DatabaseService("sqlite:///example.db")
    db_service.ensure_schema()
    
    # Create service with dependency injection
    service = ExampleService(db_service)
    
    # Create an example
    print("Creating example...")
    example = service.create_example("test", "Hello World")
    print(f"Created: {example}")
    
    # Get the example
    print("\nGetting example...")
    retrieved = service.get_example(example["id"])
    print(f"Retrieved: {retrieved}")
    
    # Update the example
    print("\nUpdating example...")
    updated = service.update_example(example["id"], "Updated Value")
    print(f"Updated: {updated}")
    
    # Check health
    from database.logic.services.healthcheck_service import HealthcheckService
    health_service = HealthcheckService(db_service)
    health = health_service.check_health()
    print(f"\nDatabase Health: {health}")
    
    # Cleanup
    db_service.close()
    print("\nDone!")
