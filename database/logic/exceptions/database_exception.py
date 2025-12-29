"""Database-related exceptions."""


class DatabaseException(Exception):
    """Base exception for all database-related errors."""
    
    def __init__(self, message: str, cause: Exception = None):
        """
        Initialize DatabaseException.
        
        Args:
            message: Error message
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.cause = cause


class ConnectionException(DatabaseException):
    """Exception raised when database connection fails."""
    pass


class SchemaException(DatabaseException):
    """Exception raised when schema operations fail."""
    pass


class SessionException(DatabaseException):
    """Exception raised when session operations fail."""
    pass


class RepositoryException(DatabaseException):
    """Exception raised when repository operations fail."""
    pass
