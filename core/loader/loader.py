"""
Loader - Application bootstrap and composition root.

Implements deterministic feature loading based on meta.json
dependency graph with topological sort.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, TYPE_CHECKING

from core.container import Container
from core.environment import AppEnv, load_config
from .feature_module import FeatureModule
from .exceptions import (
    BootstrapError,
    AuditSinkNotAvailableError,
    FeatureLoadError,
    DependencyError,
    CyclicDependencyError
)

if TYPE_CHECKING:
    from configurator.dto.feature_descriptor_dto import FeatureDescriptorDTO

logger = logging.getLogger(__name__)


# Container key constants
KEY_APP_ENV = "core.env.IAppEnv"
KEY_DATABASE_SERVICE = "core.database.IDatabaseService"
KEY_CONFIGURATOR_SERVICE = "core.configurator.IConfiguratorService"
KEY_LICENSING_SERVICE = "core.licensing.ILicensingService"
KEY_AUDIT_SERVICE = "audit.IAuditService"
KEY_AUDIT_SINK = "audit.IAuditSink"
KEY_AUTH_SERVICE = "auth.IAuthenticatorService"
KEY_USER_SERVICE = "user.IUserManagementService"
KEY_USER_REPOSITORY = "user.IUserRepository"
KEY_TRANSLATION_SERVICE = "translation.ITranslationService"


def parse_database_path(database_url: str) -> str:
    """
    Parse database path from SQLAlchemy URL.
    
    Args:
        database_url: SQLAlchemy database URL (e.g., "sqlite:///qmtool.db")
        
    Returns:
        Database file path or ":memory:" for in-memory databases
    """
    if database_url.startswith("sqlite:///"):
        return database_url[len("sqlite:///"):]
    elif database_url == "sqlite:///:memory:" or database_url == "sqlite://":
        return ":memory:"
    else:
        # Fallback for unknown formats
        logger.warning(f"Unknown database URL format: {database_url}, using audit.db")
        return "audit.db"


class Loader:
    """
    Application loader and composition root.
    
    Responsible for:
    - Loading configuration from config.ini
    - Discovering features via Configurator
    - Building dependency graph
    - Topological sort for boot order
    - Registering all features with DI container
    - Verifying audit sink availability (mandatory)
    
    Usage:
        >>> loader = Loader(config_path="config.ini")
        >>> loader.boot()
        >>> container = loader.get_container()
        >>> service = container.resolve("core.database.IDatabaseService")
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        project_root: Optional[Path] = None,
        skip_features: Optional[List[str]] = None
    ):
        """
        Initialize loader.
        
        Args:
            config_path: Path to config.ini file
            project_root: Project root directory
            skip_features: List of feature IDs to skip (for testing)
        """
        self._config_path = config_path
        self._project_root = project_root or Path.cwd()
        self._skip_features = set(skip_features or [])
        
        self._container = Container()
        self._env: Optional[AppEnv] = None
        self._boot_log: List[str] = []
        self._booted = False
    
    def boot(self) -> List[str]:
        """
        Boot the application.
        
        Returns:
            List of feature IDs in boot order
            
        Raises:
            BootstrapError: If boot fails
            AuditSinkNotAvailableError: If audit sink cannot be registered
        """
        if self._booted:
            logger.warning("Application already booted")
            return self._boot_log
        
        logger.info("Starting application boot sequence")
        
        try:
            # Step 1: Load configuration
            self._env = load_config(self._config_path, self._project_root)
            self._container.add_singleton(KEY_APP_ENV, lambda: self._env)
            logger.info("Configuration loaded")
            
            # Step 2: Register core infrastructure (TIER 0-1)
            self._register_infrastructure()
            
            # Step 3: Discover features
            features = self._discover_features()
            
            # Step 4: Build dependency graph and compute boot order
            boot_order = self._compute_boot_order(features)
            
            # Step 5: Register features in boot order
            for feature_id in boot_order:
                if feature_id in self._skip_features:
                    logger.info(f"Skipping feature: {feature_id}")
                    # If audittrail is skipped, that's a hard failure
                    if feature_id == "audittrail":
                        raise AuditSinkNotAvailableError("audittrail feature was skipped but audit is mandatory")
                    continue
                
                self._register_feature(feature_id, features.get(feature_id))
                self._boot_log.append(feature_id)
                
                # After audittrail, verify audit sink (HARD GATE)
                if feature_id == "audittrail":
                    self._verify_audit_sink()
            
            # Final verification: audit sink must be available
            if not self._container.is_registered(KEY_AUDIT_SINK):
                raise AuditSinkNotAvailableError("Audit sink was not registered")
            
            # Step 6: Start all features
            self._start_features()
            
            self._booted = True
            logger.info(f"Boot complete. Features loaded: {self._boot_log}")
            return self._boot_log
            
        except Exception as e:
            logger.error(f"Boot failed: {e}")
            raise
    
    def get_container(self) -> Container:
        """
        Get the DI container.
        
        Returns:
            Container with registered services
        """
        return self._container
    
    def get_env(self) -> AppEnv:
        """
        Get the application environment.
        
        Returns:
            AppEnv configuration
        """
        if self._env is None:
            raise BootstrapError("Application not booted yet")
        return self._env
    
    def _register_infrastructure(self) -> None:
        """Register core infrastructure services (TIER 0-1)."""
        logger.info("Registering infrastructure services")
        
        # TIER 0: Licensing (first, for license check)
        self._register_licensing()
        
        # TIER 0: Configurator (for feature discovery)
        self._register_configurator()
        
        # TIER 1: Database (core infrastructure)
        self._register_database()
    
    def _register_licensing(self) -> None:
        """Register licensing service."""
        try:
            from licensing.LOGIC.services.licensing_service import LicensingService
            from licensing.LOGIC.repositories.file_license_repository import FileLicenseRepository
            from licensing.LOGIC.fingerprint.windows_fingerprint_provider import WindowsFingerprintProvider
            
            def create_licensing_service():
                backend = FileLicenseRepository(self._env.license_path)
                fingerprint = WindowsFingerprintProvider()
                return LicensingService(backend, fingerprint)
            
            self._container.add_singleton(KEY_LICENSING_SERVICE, create_licensing_service)
            logger.info("Licensing service registered")
        except ImportError as e:
            logger.warning(f"Licensing module not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register licensing: {e}")
    
    def _register_configurator(self) -> None:
        """Register configurator service."""
        from configurator.services.configurator_service import ConfiguratorService
        from configurator.repository.feature_repository import FeatureRepository
        from configurator.repository.config_repository import ConfigRepository
        
        def create_configurator_service():
            feature_repo = FeatureRepository(str(self._env.features_root))
            config_repo = ConfigRepository(str(self._env.project_root))
            return ConfiguratorService(feature_repo, config_repo)
        
        self._container.add_singleton(KEY_CONFIGURATOR_SERVICE, create_configurator_service)
        logger.info("Configurator service registered")
    
    def _register_database(self) -> None:
        """Register database service."""
        from database.logic.services.database_service import DatabaseService
        
        def create_database_service():
            return DatabaseService(self._env.database_url, self._env.db_echo)
        
        self._container.add_singleton(KEY_DATABASE_SERVICE, create_database_service)
        logger.info("Database service registered")
    
    def _discover_features(self) -> Dict[str, "FeatureDescriptorDTO"]:
        """
        Discover features via Configurator.
        
        Returns:
            Dict mapping feature_id to FeatureDescriptorDTO
        """
        configurator = self._container.resolve(KEY_CONFIGURATOR_SERVICE)
        descriptors = configurator.discover_features()
        
        features = {d.id: d for d in descriptors}
        logger.info(f"Discovered {len(features)} features: {list(features.keys())}")
        return features
    
    def _compute_boot_order(self, features: Dict[str, "FeatureDescriptorDTO"]) -> List[str]:
        """
        Compute boot order using topological sort.
        
        Boot order is determined by:
        1. Dependencies from meta.json
        2. Implicit dependencies (audit requirement)
        3. sort_order (as tiebreaker)
        
        Args:
            features: Dict of feature descriptors
            
        Returns:
            List of feature IDs in boot order
            
        Raises:
            CyclicDependencyError: If cyclic dependency detected
        """
        # Core infrastructure features that don't depend on audittrail
        # (they can't, because audittrail depends on them)
        CORE_INFRASTRUCTURE = {"licensing", "configurator", "database"}
        
        # Build adjacency list (feature -> dependencies that exist)
        graph: Dict[str, Set[str]] = {}
        feature_ids = set(features.keys())
        
        for feature_id, descriptor in features.items():
            deps = set()
            
            # Add explicit dependencies from meta.json (only if they exist)
            for dep in descriptor.dependencies:
                if dep in feature_ids:
                    deps.add(dep)
            
            # Core infrastructure and audittrail don't add implicit deps to audittrail
            # (to avoid circular dependency)
            if feature_id not in CORE_INFRASTRUCTURE and feature_id != "audittrail":
                # All non-core features with must_audit=true depend on audittrail
                if descriptor.audit and descriptor.audit.must_audit:
                    if "audittrail" in feature_ids:
                        deps.add("audittrail")
                
                # All non-core features depend on database
                if "database" in feature_ids:
                    deps.add("database")
            
            # audittrail depends on configurator and database
            if feature_id == "audittrail":
                if "configurator" in feature_ids:
                    deps.add("configurator")
                if "database" in feature_ids:
                    deps.add("database")
            
            graph[feature_id] = deps
        
        logger.debug(f"Dependency graph: {graph}")
        
        # Topological sort using Kahn's algorithm
        # in_degree[f] = number of features that f depends on (that are still unprocessed)
        in_degree: Dict[str, int] = {f: len(graph[f]) for f in features}
        
        # Start with features that have no dependencies
        queue = [(features[f].sort_order, f) for f in features if in_degree[f] == 0]
        queue.sort()  # Sort by sort_order
        
        result = []
        
        while queue:
            _, feature_id = queue.pop(0)
            result.append(feature_id)
            
            # For all features that depend on this one, decrement their in_degree
            for other_id in features:
                if feature_id in graph[other_id]:
                    in_degree[other_id] -= 1
                    if in_degree[other_id] == 0:
                        queue.append((features[other_id].sort_order, other_id))
                        queue.sort()
        
        # Check for cycles
        if len(result) != len(features):
            remaining = [f for f in features if f not in result]
            raise CyclicDependencyError(remaining)
        
        logger.info(f"Boot order: {result}")
        return result
    
    def _register_feature(self, feature_id: str, descriptor: Optional["FeatureDescriptorDTO"]) -> None:
        """
        Register a feature's services with the container.
        
        Args:
            feature_id: Feature ID
            descriptor: Feature descriptor (may be None)
        """
        logger.info(f"Registering feature: {feature_id}")
        
        # Use feature-specific registration
        if feature_id == "audittrail":
            self._register_audittrail()
        elif feature_id == "user_management":
            self._register_user_management()
        elif feature_id == "authenticator":
            self._register_authenticator()
        elif feature_id == "translation":
            self._register_translation()
        elif feature_id in ["licensing", "configurator", "database"]:
            # Already registered in infrastructure
            pass
        else:
            logger.warning(f"No registration handler for feature: {feature_id}")
    
    def _register_audittrail(self) -> None:
        """Register audit trail service (PFLICHT!)."""
        from audittrail.services.audit_service import AuditService
        from audittrail.repository.audit_repository import AuditRepository
        from audittrail.services.policy.audit_policy import AuditPolicy
        
        def create_audit_service():
            cfg = self._container.resolve(KEY_CONFIGURATOR_SERVICE)
            db_path = parse_database_path(self._env.database_url)
            repo = AuditRepository(db_path)
            policy = AuditPolicy()
            return AuditService(repo, policy, cfg)
        
        self._container.add_singleton(KEY_AUDIT_SERVICE, create_audit_service)
        self._container.add_alias(KEY_AUDIT_SINK, KEY_AUDIT_SERVICE)
        logger.info("Audit service registered (PFLICHT)")
    
    def _register_user_management(self) -> None:
        """Register user management service."""
        from user_management.services.user_management_service import UserManagementService
        from user_management.repository.user_repository import UserRepository
        
        def create_user_repository():
            return UserRepository()
        
        def create_user_service():
            repo = self._container.resolve(KEY_USER_REPOSITORY)
            return UserManagementService(repo)
        
        self._container.add_singleton(KEY_USER_REPOSITORY, create_user_repository)
        self._container.add_singleton(KEY_USER_SERVICE, create_user_service)
        logger.info("User management service registered")
    
    def _register_authenticator(self) -> None:
        """Register authenticator service."""
        from authenticator.services.authenticator_service import AuthenticatorService
        
        def create_auth_service():
            db = self._container.resolve(KEY_DATABASE_SERVICE)
            user_repo = self._container.resolve(KEY_USER_REPOSITORY)
            return AuthenticatorService(db.get_session(), user_repo)
        
        self._container.add_singleton(KEY_AUTH_SERVICE, create_auth_service)
        logger.info("Authenticator service registered")
    
    def _register_translation(self) -> None:
        """Register translation service."""
        from translation.services.translation_service import TranslationService
        from translation.repository.translation_repository import InMemoryTranslationRepository
        from translation.services.policy.translation_policy import TranslationPolicy
        from translation.services.feature_discovery_service import FeatureDiscoveryService
        
        def create_translation_service():
            repo = InMemoryTranslationRepository()
            policy = TranslationPolicy()
            discovery = FeatureDiscoveryService(str(self._env.features_root))
            return TranslationService(repo, policy, discovery)
        
        self._container.add_singleton(KEY_TRANSLATION_SERVICE, create_translation_service)
        logger.info("Translation service registered")
    
    def _verify_audit_sink(self) -> None:
        """
        Verify audit sink is available.
        
        This is a HARD GATE - application cannot start without audit.
        
        Raises:
            AuditSinkNotAvailableError: If audit sink not registered
        """
        if not self._container.is_registered(KEY_AUDIT_SINK):
            raise AuditSinkNotAvailableError()
        
        # Try to resolve to verify it works
        try:
            audit = self._container.resolve(KEY_AUDIT_SINK)
            if audit is None:
                raise AuditSinkNotAvailableError("Audit sink resolved to None")
            logger.info("Audit sink verification passed (HARD GATE)")
        except Exception as e:
            raise AuditSinkNotAvailableError(f"Failed to resolve audit sink: {e}")
    
    def _start_features(self) -> None:
        """Start all registered features."""
        logger.info("Starting features...")
        
        # Ensure database schema is created
        if self._container.is_registered(KEY_DATABASE_SERVICE):
            try:
                db = self._container.resolve(KEY_DATABASE_SERVICE)
                db.ensure_schema()
                logger.info("Database schema ensured")
            except Exception as e:
                logger.warning(f"Failed to ensure database schema: {e}")
