"""
ConfiguratorServiceInterface - Contract für Configurator.

Definiert alle öffentlichen Methoden des Configurator-Service.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from configurator.dto.app_config_dto import AppConfigDTO
from configurator.dto.feature_descriptor_dto import FeatureDescriptorDTO
from configurator.dto.feature_registry_dto import FeatureRegistryDTO


class ConfiguratorServiceInterface(ABC):
    """
    Zentrale Schnittstelle für Feature-Discovery und Meta-Lookup (MVP).

    Verantwortlichkeiten:
    - Feature-Discovery (Scannen nach meta.json)
    - Meta-Lookup (get_feature_meta)
    - Registry-Verwaltung (get_all_features)
    - Validierung (validate_meta)
    - App-Config (get_app_config)

    Design Principles:
    - Interface-First:  Implementation ist austauschbar
    - DTO-Returns: Keine internen Entities nach außen
    - Exception-Based: Fehler werden als Exceptions geworfen

    Usage:
        >>> service = ConfiguratorService(feature_repo, config_repo)
        >>> features = service.discover_features()
        >>> auth_meta = service.get_feature_meta("authenticator")
        >>> registry = service.get_all_features(role="ADMIN")
        >>> config = service.get_app_config()
    """

    @abstractmethod
    def discover_features(self) -> List[FeatureDescriptorDTO]:
        """
        Scannt Level-1 Ordner nach `meta.json` und cached Metas.

        Prozess:
        1. Iteriert über features_root
        2. Ignoriert IGNORE_FOLDERS
        3. Lädt meta.json pro Feature
        4. Validiert meta.json
        5. Cached Descriptors

        Returns:
            Liste aller gefundenen Feature-Descriptors

        Raises:
            InvalidMetaException: Wenn meta.json ungültig ist

        Example:
            >>> features = service.discover_features()
            >>> print([f.id for f in features])
            ['authenticator', 'user_management', 'audittrail']
        """
        raise NotImplementedError

    @abstractmethod
    def get_feature_meta(self, feature_id: str) -> FeatureDescriptorDTO:
        """
        Lädt Meta für Feature oder wirft Custom Exceptions.

        Args:
            feature_id: ID des Features (muss Ordnername sein)

        Returns:
            FeatureDescriptorDTO mit vollständiger Meta-Info

        Raises:
            FeatureNotFoundException: Wenn Feature nicht existiert
            InvalidMetaException: Wenn meta.json ungültig ist

        Example:
            >>> meta = service.get_feature_meta("authenticator")
            >>> print(meta.label)  # "Authenticator"
            >>> print(meta.version)  # "1.0.0"
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_features(
            self,
            role: Optional[str] = None
    ) -> List[FeatureRegistryDTO]:
        """
        Gibt Registry-Einträge zurück, optional gefiltert nach Role/visible_for.

        Args:
            role:  Rollenname für Filterung (None = alle Features)

        Returns:
            Liste von FeatureRegistryDTO, sortiert nach sort_order und id

        Example:
            >>> # Alle Features
            >>> all_features = service.get_all_features()
            >>>
            >>> # Nur für ADMIN sichtbare Features
            >>> admin_features = service.get_all_features(role="ADMIN")
            >>>
            >>> # Nur für USER sichtbare Features
            >>> user_features = service.get_all_features(role="USER")
        """
        raise NotImplementedError

    @abstractmethod
    def validate_meta(self, feature_id: str) -> bool:
        """
        Validiert meta.json inklusive `id == Ordnername`.

        Args:
            feature_id:  ID des zu validierenden Features

        Returns:
            True wenn valid

        Raises:
            FeatureNotFoundException: Wenn Feature nicht existiert
            InvalidMetaException: Wenn meta.json ungültig ist

        Example:
            >>> try:
            ...     service.validate_meta("authenticator")
            ...      print("Meta is valid")
            ... except InvalidMetaException as e:
            ...     print(f"Validation failed: {e. reason}")
        """
        raise NotImplementedError

    @abstractmethod
    def get_app_config(self) -> AppConfigDTO:
        """
        Lädt `config/app_config.json` falls vorhanden, sonst Defaults.

        Returns:
            AppConfigDTO mit globaler Konfiguration

        Example:
            >>> config = service.get_app_config()
            >>> print(config.db_path)  # "qmtool.db"
            >>> print(config.session_timeout_minutes)  # 60
        """
        raise NotImplementedError