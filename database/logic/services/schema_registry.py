"""Schema Registry for managing database schema."""
from typing import Optional
from sqlalchemy import Engine, inspect, text
from sqlalchemy.orm import DeclarativeMeta

from ..exceptions.database_exception import SchemaException


class SchemaRegistry:
    """
    Manages database schema creation and validation.
    
    Responsible for:
    - Creating tables from SQLAlchemy models
    - Validating schema integrity
    - Future: Alembic migration integration
    """
    
    def __init__(self, engine: Engine, base: DeclarativeMeta):
        """
        Initialize SchemaRegistry.
        
        Args:
            engine: SQLAlchemy engine
            base: Declarative base containing all models
        """
        self._engine = engine
        self._base = base
    
    def ensure_schema(self) -> None:
        """
        Ensure all tables are created.
        
        Creates tables for all models registered with the Base.
        Safe to call multiple times - only creates missing tables.
        
        Raises:
            SchemaException: If schema creation fails
        """
        try:
            # Create all tables
            self._base.metadata.create_all(bind=self._engine)
        except Exception as e:
            raise SchemaException(
                f"Failed to create database schema: {str(e)}",
                cause=e
            )
    
    def validate_schema(self) -> bool:
        """
        Validate that all required tables exist.
        
        Returns:
            bool: True if all tables exist, False otherwise
        """
        try:
            inspector = inspect(self._engine)
            existing_tables = set(inspector.get_table_names())
            
            # Get all tables defined in models
            required_tables = set(self._base.metadata.tables.keys())
            
            # Check if all required tables exist
            return required_tables.issubset(existing_tables)
        except Exception:
            return False
    
    def get_table_names(self) -> list[str]:
        """
        Get list of all tables in the database.
        
        Returns:
            list[str]: List of table names
        """
        try:
            inspector = inspect(self._engine)
            return inspector.get_table_names()
        except Exception:
            return []
    
    def drop_all_tables(self) -> None:
        """
        Drop all tables from the database.
        
        WARNING: This is destructive and should only be used in tests!
        
        Raises:
            SchemaException: If dropping tables fails
        """
        try:
            self._base.metadata.drop_all(bind=self._engine)
        except Exception as e:
            raise SchemaException(
                f"Failed to drop database schema: {str(e)}",
                cause=e
            )
    
    def get_model_count(self) -> int:
        """
        Get count of registered models.
        
        Returns:
            int: Number of registered models
        """
        return len(self._base.metadata.tables)
