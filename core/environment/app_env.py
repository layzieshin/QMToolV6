"""
AppEnv - Application Environment configuration.

Holds all configuration values loaded from config.ini.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AppEnv:
    """
    Application environment configuration.
    
    Loaded from config.ini and provides typed access to all
    configuration values needed by the application.
    
    Attributes:
        database_url: SQLAlchemy database URL
        db_echo: Whether to echo SQL statements
        license_path: Path to license file
        public_key_path: Path to public key for license verification
        features_root: Root directory for feature discovery
        project_root: Project root directory
        data_dir: Data directory for runtime data
        global_retention_days: Default retention days for audit logs
        min_log_level: Minimum log level for audit
        session_timeout_minutes: Session timeout in minutes
    """
    
    # Database configuration
    database_url: str = "sqlite:///qmtool.db"
    db_echo: bool = False
    
    # Licensing configuration
    license_path: str = ""
    public_key_path: str = "assets/licensing/public_key.pem"
    
    # Paths
    features_root: Path = field(default_factory=lambda: Path("."))
    project_root: Path = field(default_factory=lambda: Path("."))
    data_dir: Path = field(default_factory=lambda: Path("data"))
    
    # Audit configuration
    global_retention_days: int = 365
    min_log_level: str = "INFO"
    
    # Session configuration
    session_timeout_minutes: int = 1440  # 24 hours
    
    def __post_init__(self):
        """Convert string paths to Path objects if needed."""
        if isinstance(self.features_root, str):
            self.features_root = Path(self.features_root)
        if isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
