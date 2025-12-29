"""Unit of Work implementation for transaction management."""
from typing import Type, TypeVar, Generic
from sqlalchemy.orm import Session

from .database_service_interface import UnitOfWorkInterface
from ..exceptions.transaction_exception import CommitException, RollbackException, UnitOfWorkException

T = TypeVar('T')


class UnitOfWork(UnitOfWorkInterface):
    """
    Unit of Work pattern implementation.
    
    Manages transactional boundaries and repository lifecycle.
    Used as a context manager for automatic transaction management.
    
    Usage:
        with unit_of_work as uow:
            repo = SomeRepository(uow.get_session())
            repo.create(...)
            # Auto-commits on successful exit
            # Auto-rolls back on exception
    """
    
    def __init__(self, session: Session, auto_commit: bool = True):
        """
        Initialize Unit of Work.
        
        Args:
            session: SQLAlchemy session to manage
            auto_commit: Whether to auto-commit on context exit (default: True)
        """
        self._session = session
        self._auto_commit = auto_commit
        self._committed = False
        self._rolled_back = False
    
    def __enter__(self) -> 'UnitOfWork':
        """Enter the Unit of Work context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit the Unit of Work context.
        
        Auto-commits if no exception occurred and auto_commit is True.
        Auto-rolls back if an exception occurred.
        
        Returns:
            bool: False to propagate exceptions
        """
        try:
            if exc_type is not None:
                # Exception occurred, rollback
                if not self._rolled_back:
                    self.rollback()
            else:
                # No exception, auto-commit if enabled and not already committed
                if self._auto_commit and not self._committed:
                    self.commit()
        except Exception:
            # If commit/rollback fails, ensure rollback
            if not self._rolled_back:
                try:
                    self.rollback()
                except Exception:
                    pass
        
        # Return False to propagate any exceptions
        return False
    
    def commit(self) -> None:
        """
        Commit the current transaction.
        
        Raises:
            CommitException: If commit fails
        """
        if self._committed:
            return  # Already committed
        
        if self._rolled_back:
            raise UnitOfWorkException("Cannot commit after rollback")
        
        try:
            self._session.commit()
            self._committed = True
        except Exception as e:
            # Attempt rollback on commit failure
            try:
                self._session.rollback()
                self._rolled_back = True
            except Exception:
                pass
            
            raise CommitException(
                f"Transaction commit failed: {str(e)}",
                cause=e
            )
    
    def rollback(self) -> None:
        """
        Rollback the current transaction.
        
        Raises:
            RollbackException: If rollback fails
        """
        if self._rolled_back:
            return  # Already rolled back
        
        try:
            self._session.rollback()
            self._rolled_back = True
        except Exception as e:
            raise RollbackException(
                f"Transaction rollback failed: {str(e)}",
                cause=e
            )
    
    def get_session(self) -> Session:
        """
        Get the SQLAlchemy session for this Unit of Work.
        
        Returns:
            Session: The managed session
        """
        return self._session
    
    @property
    def is_committed(self) -> bool:
        """Check if transaction is committed."""
        return self._committed
    
    @property
    def is_rolled_back(self) -> bool:
        """Check if transaction is rolled back."""
        return self._rolled_back
