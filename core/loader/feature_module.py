"""
FeatureModule - Base class for feature modules.

Each feature provides a FeatureModule that knows how to register
its services with the DI container.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.container import Container
    from core.environment import AppEnv


class FeatureModule(ABC):
    """
    Base class for feature modules.
    
    Each feature should provide a class that extends FeatureModule
    and implements the register() method to register its services
    with the DI container.
    
    Usage:
        class DatabaseModule(FeatureModule):
            @property
            def feature_id(self) -> str:
                return "database"
            
            def register(self, container: Container, env: AppEnv) -> None:
                container.add_singleton(
                    "core.database.IDatabaseService",
                    lambda: DatabaseService(env.database_url)
                )
    """
    
    @property
    @abstractmethod
    def feature_id(self) -> str:
        """
        Return the feature ID.
        
        This must match the feature folder name and meta.json id.
        """
        pass
    
    @abstractmethod
    def register(self, container: "Container", env: "AppEnv") -> None:
        """
        Register feature services with the container.
        
        Args:
            container: DI container to register services with
            env: Application environment configuration
        """
        pass
    
    def start(self, container: "Container") -> None:
        """
        Called after all features are registered.
        
        Override this method to perform any startup tasks that
        require other services to be available.
        
        Args:
            container: DI container with all services registered
        """
        pass
