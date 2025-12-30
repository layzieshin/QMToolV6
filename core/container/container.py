"""
DI Container implementation.

Minimal DI Container with singleton and factory support.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

import logging
from typing import Callable, Any, Dict, Set, Optional
from enum import Enum
from dataclasses import dataclass

from .exceptions import ServiceNotFoundError, CircularDependencyError, ServiceAlreadyRegisteredError

logger = logging.getLogger(__name__)


class Lifetime(Enum):
    """Service lifetime."""
    SINGLETON = "singleton"
    FACTORY = "factory"


@dataclass
class ServiceDescriptor:
    """Describes a registered service."""
    key: str
    factory: Callable[[], Any]
    lifetime: Lifetime
    instance: Optional[Any] = None


class Container:
    """
    Minimal DI Container.
    
    Supports:
    - Singleton registration (single instance, lazily created)
    - Factory registration (new instance per resolve)
    - Circular dependency detection
    - Service lookup by key
    
    Usage:
        >>> container = Container()
        >>> container.add_singleton("db", lambda: DatabaseService())
        >>> container.add_factory("uow", lambda: UnitOfWork())
        >>> db = container.resolve("db")  # Same instance every time
        >>> uow = container.resolve("uow")  # New instance every time
    """
    
    def __init__(self):
        """Initialize empty container."""
        self._services: Dict[str, ServiceDescriptor] = {}
        self._resolving: Set[str] = set()  # Track currently resolving services
        logger.debug("Container initialized")
    
    def add_singleton(self, key: str, factory: Callable[[], Any]) -> None:
        """
        Register a singleton service.
        
        The factory is called once on first resolve, then the same
        instance is returned for all subsequent resolves.
        
        Args:
            key: Service key (e.g., "core.database.IDatabaseService")
            factory: Factory function that creates the service instance
            
        Raises:
            ServiceAlreadyRegisteredError: If key is already registered
        """
        if key in self._services:
            raise ServiceAlreadyRegisteredError(key)
        
        self._services[key] = ServiceDescriptor(
            key=key,
            factory=factory,
            lifetime=Lifetime.SINGLETON,
            instance=None
        )
        logger.debug(f"Registered singleton: {key}")
    
    def add_factory(self, key: str, factory: Callable[[], Any]) -> None:
        """
        Register a factory service.
        
        The factory is called every time the service is resolved,
        returning a new instance each time.
        
        Args:
            key: Service key
            factory: Factory function that creates service instances
            
        Raises:
            ServiceAlreadyRegisteredError: If key is already registered
        """
        if key in self._services:
            raise ServiceAlreadyRegisteredError(key)
        
        self._services[key] = ServiceDescriptor(
            key=key,
            factory=factory,
            lifetime=Lifetime.FACTORY,
            instance=None
        )
        logger.debug(f"Registered factory: {key}")
    
    def add_alias(self, alias_key: str, target_key: str) -> None:
        """
        Register an alias for an existing service.
        
        Args:
            alias_key: The new key (alias)
            target_key: The existing service key to alias
            
        Raises:
            ServiceAlreadyRegisteredError: If alias_key is already registered
            ServiceNotFoundError: If target_key doesn't exist
        """
        if alias_key in self._services:
            raise ServiceAlreadyRegisteredError(alias_key)
        
        if target_key not in self._services:
            raise ServiceNotFoundError(target_key)
        
        # Store target_key in closure explicitly for clarity
        def create_alias_resolver(target: str):
            """Create a resolver function for the alias."""
            return lambda: self.resolve(target)
        
        self._services[alias_key] = ServiceDescriptor(
            key=alias_key,
            factory=create_alias_resolver(target_key),
            lifetime=Lifetime.SINGLETON,  # Alias resolves to same instance
            instance=None
        )
        logger.debug(f"Registered alias: {alias_key} -> {target_key}")
    
    def resolve(self, key: str) -> Any:
        """
        Resolve a service by key.
        
        Args:
            key: Service key
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotFoundError: If service is not registered
            CircularDependencyError: If circular dependency detected
        """
        if key not in self._services:
            raise ServiceNotFoundError(key)
        
        # Circular dependency check
        if key in self._resolving:
            raise CircularDependencyError(key, list(self._resolving))
        
        descriptor = self._services[key]
        
        # For singletons, return cached instance if available
        if descriptor.lifetime == Lifetime.SINGLETON and descriptor.instance is not None:
            return descriptor.instance
        
        # Mark as resolving (for circular dependency detection)
        self._resolving.add(key)
        
        try:
            instance = descriptor.factory()
            
            # Cache singleton instances
            if descriptor.lifetime == Lifetime.SINGLETON:
                descriptor.instance = instance
            
            logger.debug(f"Resolved: {key}")
            return instance
            
        finally:
            self._resolving.discard(key)
    
    def try_resolve(self, key: str) -> Optional[Any]:
        """
        Try to resolve a service, returning None if not found.
        
        Args:
            key: Service key
            
        Returns:
            Service instance or None if not found
        """
        try:
            return self.resolve(key)
        except ServiceNotFoundError:
            return None
    
    def is_registered(self, key: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            key: Service key
            
        Returns:
            True if registered
        """
        return key in self._services
    
    def get_all_keys(self) -> list:
        """
        Get all registered service keys.
        
        Returns:
            List of service keys
        """
        return list(self._services.keys())
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._resolving.clear()
        logger.debug("Container cleared")
