"""
Container exceptions.

Author: QMToolV6 Development Team
Version: 1.0.0
"""


class ContainerException(Exception):
    """Base exception for container errors."""
    pass


class ServiceNotFoundError(ContainerException):
    """Raised when a service is not found in the container."""
    
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Service not found: {key}")


class CircularDependencyError(ContainerException):
    """Raised when a circular dependency is detected."""
    
    def __init__(self, key: str, chain: list):
        self.key = key
        self.chain = chain
        super().__init__(f"Circular dependency detected: {' -> '.join(chain)} -> {key}")


class ServiceAlreadyRegisteredError(ContainerException):
    """Raised when trying to register a service that already exists."""
    
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Service already registered: {key}")
