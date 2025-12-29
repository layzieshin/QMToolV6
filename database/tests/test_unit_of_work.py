"""Tests for UnitOfWork."""
import pytest

from database.logic.services.unit_of_work import UnitOfWork
from database.logic.exceptions.transaction_exception import CommitException, UnitOfWorkException


class TestUnitOfWork:
    """Tests for UnitOfWork."""
    
    def test_initialization(self, db_session):
        """Test Unit of Work initialization."""
        # Act
        uow = UnitOfWork(db_session)
        
        # Assert
        assert uow is not None
        assert uow.get_session() is db_session
    
    def test_context_manager(self, db_session):
        """Test Unit of Work as context manager."""
        # Act
        with UnitOfWork(db_session) as uow:
            assert uow is not None
    
    def test_commit(self, db_session):
        """Test explicit commit."""
        from database.tests.conftest import SampleEntity
        
        # Arrange
        uow = UnitOfWork(db_session, auto_commit=False)
        
        # Act
        with uow:
            session = uow.get_session()
            entity = SampleEntity(name="Commit Test", description="Testing commit")
            session.add(entity)
            uow.commit()
        
        # Assert
        result = db_session.query(SampleEntity).filter_by(name="Commit Test").first()
        assert result is not None
    
    def test_rollback(self, db_session):
        """Test explicit rollback."""
        from database.tests.conftest import SampleEntity
        
        # Arrange
        uow = UnitOfWork(db_session, auto_commit=False)
        
        # Act
        with uow:
            session = uow.get_session()
            entity = SampleEntity(name="Rollback Test", description="Testing rollback")
            session.add(entity)
            uow.rollback()
        
        # Assert
        result = db_session.query(SampleEntity).filter_by(name="Rollback Test").first()
        assert result is None
    
    def test_auto_commit_on_success(self, db_session):
        """Test auto-commit on successful context exit."""
        from database.tests.conftest import SampleEntity
        
        # Act
        with UnitOfWork(db_session, auto_commit=True):
            entity = SampleEntity(name="Auto Commit", description="Testing auto commit")
            db_session.add(entity)
        
        # Assert
        result = db_session.query(SampleEntity).filter_by(name="Auto Commit").first()
        assert result is not None
    
    def test_auto_rollback_on_exception(self, db_session):
        """Test auto-rollback on exception."""
        from database.tests.conftest import SampleEntity
        
        # Act & Assert
        with pytest.raises(ValueError):
            with UnitOfWork(db_session, auto_commit=True):
                entity = SampleEntity(name="Exception Test", description="Testing exception")
                db_session.add(entity)
                raise ValueError("Simulated error")
        
        # Assert - should be rolled back
        result = db_session.query(SampleEntity).filter_by(name="Exception Test").first()
        assert result is None
    
    def test_cannot_commit_after_rollback(self, db_session):
        """Test that commit fails after rollback."""
        # Arrange
        uow = UnitOfWork(db_session, auto_commit=False)
        
        # Act & Assert
        with uow:
            uow.rollback()
            with pytest.raises(UnitOfWorkException):
                uow.commit()
    
    def test_is_committed_flag(self, db_session):
        """Test is_committed property."""
        # Arrange
        uow = UnitOfWork(db_session, auto_commit=False)
        
        # Assert initial state
        assert not uow.is_committed
        
        # Act
        with uow:
            uow.commit()
        
        # Assert
        assert uow.is_committed
    
    def test_is_rolled_back_flag(self, db_session):
        """Test is_rolled_back property."""
        # Arrange
        uow = UnitOfWork(db_session, auto_commit=False)
        
        # Assert initial state
        assert not uow.is_rolled_back
        
        # Act
        with uow:
            uow.rollback()
        
        # Assert
        assert uow.is_rolled_back
