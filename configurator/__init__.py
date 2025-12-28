"""
Configurator Package

Feature-Discovery, Meta-Validierung und App-Konfiguration.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from configurator.services.configurator_service import ConfiguratorService
from configurator.repository.feature_repository import FeatureRepository
from configurator.repository.config_repository import ConfigRepository

__version__ = "1.0.0"

__all__ = [
    "ConfiguratorService",
    "FeatureRepository",
    "ConfigRepository",
]