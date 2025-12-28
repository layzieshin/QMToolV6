"""
Shared Test Fixtures für Configurator.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

import pytest

from configurator.repository.config_repository import ConfigRepository
from configurator.repository.feature_repository import FeatureRepository
from configurator.services.configurator_service import ConfiguratorService


@pytest.fixture
def temp_features_root(tmp_path: Path) -> Path:
    """
    Erstellt temporäres Feature-Root-Verzeichnis.

    Returns:
        Path zum temp-Verzeichnis
    """
    return tmp_path


@pytest.fixture
def feature_repository(temp_features_root: Path) -> FeatureRepository:
    """
    Erstellt FeatureRepository mit temp-Root.

    Returns:
        FeatureRepository-Instanz
    """
    return FeatureRepository(features_root=str(temp_features_root))


@pytest.fixture
def config_repository(temp_features_root: Path) -> ConfigRepository:
    """
    Erstellt ConfigRepository mit temp-Root.

    Returns:
        ConfigRepository-Instanz
    """
    return ConfigRepository(project_root=str(temp_features_root))


@pytest.fixture
def configurator_service(
        feature_repository: FeatureRepository,
        config_repository: ConfigRepository
) -> ConfiguratorService:
    """
    Erstellt ConfiguratorService mit temp-Repositories.

    Returns:
        ConfiguratorService-Instanz
    """
    return ConfiguratorService(feature_repository, config_repository)


def create_meta_json(
        folder: Path,
        meta_data: Dict[str, Any]
) -> None:
    """
    Helper:  Erstellt meta.json in Ordner.

    Args:
        folder: Ziel-Ordner
        meta_data: Dict mit Meta-Daten
    """
    folder.mkdir(parents=True, exist_ok=True)
    meta_path = folder / "meta.json"
    meta_path.write_text(
        json.dumps(meta_data, indent=2),
        encoding="utf-8"
    )


def create_app_config_json(
        project_root: Path,
        config_data: Dict[str, Any]
) -> None:
    """
    Helper: Erstellt config/app_config.json.

    Args:
        project_root: Projekt-Root
        config_data:  Dict mit Config-Daten
    """
    config_dir = project_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "app_config.json"
    config_path.write_text(
        json.dumps(config_data, indent=2),
        encoding="utf-8"
    )


@pytest.fixture
def sample_feature_meta() -> Dict[str, Any]:
    """
    Sample Feature meta. json.

    Returns:
        Dict mit gültigen Meta-Daten
    """
    return {
        "id": "authenticator",
        "label": "Authenticator",
        "version": "1.0.0",
        "main_class": "authenticator.services.authenticator_service.AuthenticatorService",
        "visible_for": ["ADMIN", "USER"],
        "is_core": True,
        "sort_order": 10,
        "requires_login": False,
        "dependencies": [],
        "audit": {
            "must_audit": True,
            "min_log_level": "INFO",
            "critical_actions": ["LOGIN", "LOGOUT"],
            "retention_days": 365
        },
        "description": "Session-based authentication",
        "icon": "lock-icon.svg"
    }


@pytest.fixture
def sample_app_config() -> Dict[str, Any]:
    """
    Sample app_config.json.

    Returns:
        Dict mit gültiger App-Config
    """
    return {
        "app_name": "QMToolV6",
        "app_version": "1.0.0",
        "database": {
            "path": "test.db"
        },
        "audit": {
            "default_log_level": "DEBUG",
            "default_retention_days": 90
        },
        "session": {
            "timeout_minutes": 30,
            "max_failed_logins": 3
        },
        "paths": {
            "features_root": ".",
            "data_dir": "./test_data",
            "temp_dir": "./test_temp"
        }
    }