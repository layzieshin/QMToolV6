"""
Integration tests for bootstrap and boot sequence.

Tests:
- Deterministic boot order
- Audit sink hard-fail gate
- All features registration

Author: QMToolV6 Development Team
Version: 1.0.0
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.loader import Loader, AuditSinkNotAvailableError
from core.container import Container


class TestBootstrap:
    """Tests for bootstrap sequence."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent
    
    def test_container_basic_operations(self):
        """Test basic container operations."""
        container = Container()
        
        # Test singleton registration
        container.add_singleton("test.singleton", lambda: {"value": 42})
        result1 = container.resolve("test.singleton")
        result2 = container.resolve("test.singleton")
        assert result1 is result2  # Same instance
        assert result1["value"] == 42
        
        # Test factory registration
        container.add_factory("test.factory", lambda: {"value": 42})
        result3 = container.resolve("test.factory")
        result4 = container.resolve("test.factory")
        assert result3 is not result4  # Different instances
        assert result3["value"] == 42
    
    def test_container_alias(self):
        """Test container alias functionality."""
        container = Container()
        
        container.add_singleton("original", lambda: {"name": "original"})
        container.add_alias("alias", "original")
        
        original = container.resolve("original")
        aliased = container.resolve("alias")
        
        assert original is aliased
    
    def test_container_service_not_found(self):
        """Test container raises on unknown service."""
        from core.container.exceptions import ServiceNotFoundError
        
        container = Container()
        
        with pytest.raises(ServiceNotFoundError):
            container.resolve("non.existent")
    
    def test_container_is_registered(self):
        """Test is_registered check."""
        container = Container()
        
        assert not container.is_registered("test.service")
        container.add_singleton("test.service", lambda: "value")
        assert container.is_registered("test.service")
    
    def test_boot_order_deterministic(self, project_root):
        """Verify features boot in correct dependency order."""
        loader = Loader(
            config_path=str(project_root / "config.ini"),
            project_root=project_root
        )
        
        boot_log = loader.boot()
        
        # Verify core infrastructure boots first
        # licensing, configurator, database should be first (or excluded if not found)
        assert len(boot_log) > 0
        
        # Verify audittrail boots before features that require it
        if "audittrail" in boot_log and "user_management" in boot_log:
            audit_idx = boot_log.index("audittrail")
            user_idx = boot_log.index("user_management")
            assert audit_idx < user_idx, "audittrail must boot before user_management"
        
        if "audittrail" in boot_log and "authenticator" in boot_log:
            audit_idx = boot_log.index("audittrail")
            auth_idx = boot_log.index("authenticator")
            assert audit_idx < auth_idx, "audittrail must boot before authenticator"
    
    def test_audit_sink_available_after_boot(self, project_root):
        """Verify IAuditSink is registered after boot."""
        loader = Loader(
            config_path=str(project_root / "config.ini"),
            project_root=project_root
        )
        
        loader.boot()
        container = loader.get_container()
        
        # Should have audit.IAuditSink registered
        assert container.is_registered("audit.IAuditSink")
        
        # Should be resolvable
        audit = container.try_resolve("audit.IAuditSink")
        assert audit is not None
    
    def test_all_core_services_registered(self, project_root):
        """Verify all core services are registered after boot."""
        loader = Loader(
            config_path=str(project_root / "config.ini"),
            project_root=project_root
        )
        
        loader.boot()
        container = loader.get_container()
        
        # Core services should be registered
        core_services = [
            "core.env.IAppEnv",
            "core.database.IDatabaseService",
            "core.configurator.IConfiguratorService",
            "audit.IAuditService",
        ]
        
        for key in core_services:
            assert container.is_registered(key), f"Service {key} not registered"
    
    def test_env_loaded_from_config(self, project_root):
        """Test environment is loaded from config.ini."""
        loader = Loader(
            config_path=str(project_root / "config.ini"),
            project_root=project_root
        )
        
        loader.boot()
        env = loader.get_env()
        
        assert env is not None
        assert env.database_url == "sqlite:///qmtool.db"
        assert env.min_log_level == "INFO"
        assert env.global_retention_days == 365


class TestAuditHardGate:
    """Tests for audit hard-fail gate."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent
    
    def test_audit_sink_not_available_raises(self, project_root):
        """If audittrail fails to register, boot must fail."""
        loader = Loader(
            config_path=str(project_root / "config.ini"),
            project_root=project_root,
            skip_features=["audittrail"]
        )
        
        # Boot should raise AuditSinkNotAvailableError
        with pytest.raises(AuditSinkNotAvailableError):
            loader.boot()
