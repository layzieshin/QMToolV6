"""Transaction-related exceptions."""
from .database_exception import DatabaseException


class TransactionException(DatabaseException):
    """Base exception for transaction-related errors."""
    pass


class CommitException(TransactionException):
    """Exception raised when transaction commit fails."""
    pass


class RollbackException(TransactionException):
    """Exception raised when transaction rollback fails."""
    pass


class UnitOfWorkException(TransactionException):
    """Exception raised when Unit-of-Work operations fail."""
    pass
