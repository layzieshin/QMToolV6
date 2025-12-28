"""
ConfiguratorService - Implementierung des Configurator-Service.

Zentrale Service-Klasse für Feature-Discovery und Konfiguration.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

import logging
from typing import List, Optional

from configurator.dto.app_config_dto import AppConfigDTO
from configurator.dto.feature_descriptor_dto import FeatureDescriptorDTO
from configurator.dto.feature_registry_dto import FeatureRegistryDTO
from configurator.repository.config_repository import ConfigRepository
from configurator.repository.feature_repository import FeatureRepository
from configurator.services.configurator_service_interface import ConfiguratorServiceInterface

logger = logging.getLogger(__name__)


class ConfiguratorService(ConfiguratorServiceInterface):
    """
    MVP-Implementierung:  Discovery, Meta-Lookup, Validation, read-only AppConfig.

    Verantwortlichkeiten:
    - Feature-Discovery über FeatureRepository
    - Meta-Lookup mit Caching
    - Registry-Verwaltung (Feature-Liste für UI)
    - Rollen-basierte Filterung (visible_for)
    - App-Config laden

    Usage:
        >>> feature_repo = FeatureRepository(features_root=".")
        >>> config_repo = ConfigRepository(project_root=".")
        >>> service = ConfiguratorService(feature_repo, config_repo)
        >>>
        >>> # Features discovern
        >>> features = service.discover_features()
        >>>
        >>> # Meta abrufen
        >>> meta = service.get_feature_meta("authenticator")
        >>>
        >>> # Registry für UI (gefiltert nach Rolle)
        >>> admin_features = service.get_all_features(role="ADMIN")
        >>>
        >>> # App-Config
        >>> config = service.get_app_config()
    """

    def __init__(
            self,
            feature_repository: FeatureRepository,
            config_repository: ConfigRepository
    ):
        """
        Initialisiert Service.

        Args:
            feature_repository: Repository für Feature-Discovery
            config_repository: Repository für App-Config
        """
        self._feature_repository = feature_repository
        self._config_repository = config_repository
        logger.info("ConfiguratorService initialized")

    def discover_features(self) -> List[FeatureDescriptorDTO]:
        """
        Scannt Level-1 Ordner nach `meta.json` und cached Metas.

        Returns:
            Liste aller gefundenen Feature-Descriptors

        Raises:
            InvalidMetaException: Wenn meta. json ungültig ist
        """
        logger.info("Starting feature discovery")
        descriptors = self._feature_repository.discover_all()
        logger.info(f"Discovered {len(descriptors)} features")
        return descriptors

    def get_feature_meta(self, feature_id: str) -> FeatureDescriptorDTO:
        """
        Lädt Meta für Feature oder wirft Custom Exceptions.

        Args:
            feature_id: ID des Features

        Returns:
            FeatureDescriptorDTO

        Raises:
            FeatureNotFoundException: Wenn Feature nicht existiert
            InvalidMetaException: Wenn meta.json ungültig ist
        """
        logger.debug(f"Loading meta for feature:  {feature_id}")
        return self._feature_repository.get_by_id(feature_id)

    def get_all_features(
            self,
            role: Optional[str] = None
    ) -> List[FeatureRegistryDTO]:
        """
        Gibt Registry-Einträge zurück, optional gefiltert nach Role/visible_for.

        Prozess:
        1. Discover all features
        2. Filter nach role (falls angegeben)
        3. Sortiere nach sort_order, dann id
        4. Wrappen in FeatureRegistryDTO

        Args:
            role: Rollenname für Filterung (None = alle)

        Returns:
            Sortierte Liste von FeatureRegistryDTO
        """
        logger.info(f"Getting all features for role:  {role or 'ALL'}")

        # Discovery
        descriptors = self._feature_repository.discover_all()

        # Rollen-Filter
        if role is not None:
            role_upper = str(role).upper()
            descriptors = [
                d for d in descriptors
                if d.is_visible_for_role(role_upper)
            ]
            logger.debug(
                f"Filtered to {len(descriptors)} features visible for role {role}"
            )

        # Sortierung:  sort_order (aufsteigend), dann id (alphabetisch)
        descriptors = sorted(
            descriptors,
            key=lambda d: (d.sort_order, d.id)
        )

        # In Registry-DTOs wrappen
        registry_dtos = [
            FeatureRegistryDTO(descriptor=d)
            for d in descriptors
        ]

        logger.info(f"Returning {len(registry_dtos)} features")
        return registry_dtos

    def validate_meta(self, feature_id: str) -> bool:
        """
        Validiert meta.json inklusive `id == Ordnername`.

        Args:
            feature_id: ID des zu validierenden Features

        Returns:
            True wenn valid

        Raises:
            FeatureNotFoundException: Wenn Feature nicht existiert
            InvalidMetaException:  Wenn meta.json ungültig ist
        """
        logger.info(f"Validating meta for feature: {feature_id}")
        return self._feature_repository.validate(feature_id)

    def get_app_config(self) -> AppConfigDTO:
        """
        Lädt `config/app_config.json` falls vorhanden, sonst Defaults.

        Returns:
            AppConfigDTO
        """
        logger.info("Loading app config")
        return self._config_repository.load_app_config()