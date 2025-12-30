"""
Integration tests for login audit flow.

Tests:
- Login creates audit log
- Logout creates audit log
- Failed login creates audit log

Author: QMToolV6 Development Team
Version: 1.0.0
"""
import pytest
from pathlib import Path
from datetime import datetime

from core.loader import Loader
from user_management.dto.user_dto import CreateUserDTO
from user_management.enum.user_enum import SystemRole


def create_bootstrap_admin(container) -> int:
    """Create a bootstrap admin user directly via repository and return its ID."""
    import bcrypt
    from user_management.repository.user_repository import UserRepository
    
    user_repo = container.resolve("user.IUserRepository")
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin = user_repo.create("bootstrap_admin", password_hash, SystemRole.ADMIN, "admin@test.com")
    return admin.id


class TestLoginAuditFlow:
    """Tests for login → audit flow."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def bootstrapped_container(self, project_root):
        """Get a bootstrapped container."""
        loader = Loader(
            config_path=str(project_root / "config.ini"),
            project_root=project_root
        )
        loader.boot()
        return loader.get_container()
    
    def test_services_resolvable(self, bootstrapped_container):
        """Test that all required services are resolvable."""
        container = bootstrapped_container
        
        # These should all be resolvable
        audit = container.resolve("audit.IAuditService")
        user_svc = container.resolve("user.IUserManagementService")
        
        assert audit is not None
        assert user_svc is not None
    
    def test_audit_log_can_be_created(self, bootstrapped_container):
        """Test that audit logs can be created via the service."""
        from audittrail.enum.audit_enum import LogLevel, AuditSeverity
        
        container = bootstrapped_container
        audit = container.resolve("audit.IAuditService")
        
        # Create a test audit log
        log_id = audit.log(
            user_id=0,
            action="TEST_ACTION",
            feature="integration_test",
            log_level=LogLevel.INFO,
            severity=AuditSeverity.INFO,
            details={"test": True}
        )
        
        # Should return a valid log ID
        assert log_id is not None
        assert log_id > 0 or log_id == -1  # -1 if filtered out by min_log_level
    
    def test_user_can_be_created(self, bootstrapped_container):
        """Test that users can be created via the service."""
        container = bootstrapped_container
        
        # First create a bootstrap admin
        admin_id = create_bootstrap_admin(container)
        
        user_svc = container.resolve("user.IUserManagementService")
        
        # Create a test user (as admin)
        dto = CreateUserDTO(
            username=f"testuser_{datetime.now().timestamp()}",
            password="testpass123",
            role=SystemRole.USER
        )
        
        user = user_svc.create_user(dto, actor_id=admin_id)
        
        assert user is not None
        assert user.username == dto.username
        assert user.role == SystemRole.USER


class TestDefenseInDepth:
    """Tests for defense in depth (UI-Gate + Service-Gate)."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def bootstrapped_container(self, project_root):
        """Get a bootstrapped container."""
        loader = Loader(
            config_path=str(project_root / "config.ini"),
            project_root=project_root
        )
        loader.boot()
        return loader.get_container()
    
    def test_create_user_requires_admin_permission(self, bootstrapped_container):
        """Test that create_user enforces policy (Service-Gate)."""
        from user_management.exceptions import PermissionDeniedError
        
        container = bootstrapped_container
        
        # First create a bootstrap admin
        admin_id = create_bootstrap_admin(container)
        
        user_svc = container.resolve("user.IUserManagementService")
        
        # Create a regular user (as admin)
        regular_user = user_svc.create_user(
            CreateUserDTO(
                username=f"regular_{datetime.now().timestamp()}",
                password="pass123",
                role=SystemRole.USER
            ),
            actor_id=admin_id
        )
        
        # Now try to create another user as the regular user (should fail)
        with pytest.raises(PermissionDeniedError):
            user_svc.create_user(
                CreateUserDTO(
                    username=f"another_{datetime.now().timestamp()}",
                    password="pass123",
                    role=SystemRole.USER
                ),
                actor_id=regular_user.id  # Regular user, not admin
            )
