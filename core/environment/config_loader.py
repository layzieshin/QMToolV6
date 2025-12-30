"""
Config Loader - Loads configuration from config.ini.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

import configparser
import logging
import os
from pathlib import Path
from typing import Optional

from .app_env import AppEnv

logger = logging.getLogger(__name__)


class ConfigLoadError(Exception):
    """Raised when config.ini cannot be loaded or parsed."""
    pass


def load_config(config_path: Optional[str] = None, project_root: Optional[Path] = None) -> AppEnv:
    """
    Load configuration from config.ini.
    
    Args:
        config_path: Path to config.ini file. If None, searches in project_root.
        project_root: Project root directory. Defaults to current directory.
        
    Returns:
        AppEnv with loaded configuration
        
    Raises:
        ConfigLoadError: If config file is invalid
    """
    if project_root is None:
        project_root = Path.cwd()
    
    # Find config file
    if config_path is None:
        config_file = project_root / "config.ini"
    else:
        config_file = Path(config_path)
    
    # Create default AppEnv if no config file exists
    if not config_file.exists():
        logger.warning(f"Config file not found at {config_file}, using defaults")
        return AppEnv(
            features_root=project_root,
            project_root=project_root
        )
    
    # Parse config file
    parser = configparser.ConfigParser()
    
    try:
        parser.read(config_file, encoding="utf-8")
    except configparser.Error as e:
        raise ConfigLoadError(f"Failed to parse config.ini: {e}")
    
    # Build AppEnv from config
    env = AppEnv()
    
    # [database] section
    if parser.has_section("database"):
        env.database_url = parser.get("database", "url", fallback=env.database_url)
        env.db_echo = parser.getboolean("database", "echo", fallback=env.db_echo)
    
    # [licensing] section
    if parser.has_section("licensing"):
        license_path = parser.get("licensing", "license_path", fallback="")
        # Expand environment variables (e.g., %PROGRAMDATA%)
        env.license_path = _expand_path(license_path)
        env.public_key_path = parser.get("licensing", "public_key_path", fallback=env.public_key_path)
    
    # [paths] section
    if parser.has_section("paths"):
        features_root = parser.get("paths", "features_root", fallback=".")
        env.features_root = Path(features_root)
        if not env.features_root.is_absolute():
            env.features_root = project_root / env.features_root
        
        env.project_root = project_root
        
        data_dir = parser.get("paths", "data_dir", fallback="data")
        env.data_dir = Path(data_dir)
        if not env.data_dir.is_absolute():
            env.data_dir = project_root / env.data_dir
    else:
        env.features_root = project_root
        env.project_root = project_root
    
    # [audit] section
    if parser.has_section("audit"):
        env.global_retention_days = parser.getint("audit", "global_retention_days", fallback=env.global_retention_days)
        env.min_log_level = parser.get("audit", "min_log_level", fallback=env.min_log_level)
    
    # [session] section
    if parser.has_section("session"):
        env.session_timeout_minutes = parser.getint("session", "timeout_minutes", fallback=env.session_timeout_minutes)
    
    logger.info(f"Loaded config from {config_file}")
    return env


def _expand_path(path: str) -> str:
    """Expand environment variables in path."""
    # Handle Windows-style %VAR% placeholders
    result = path
    for key, value in os.environ.items():
        result = result.replace(f"%{key}%", value)
    # Also handle Unix-style $VAR placeholders
    result = os.path.expandvars(result)
    return result
