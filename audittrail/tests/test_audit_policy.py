"""
Unit Tests für AuditPolicy

Testet Zugriffskontroll-Regeln:
- can_read_logs()
- can_export_logs()
- Admin/QMB vs. normaler User

Author: QMToolV6 Development Team
Version: 1.0.0
"""
import pytest

from audittrail.services.policy.audit_policy import AuditPolicy
from audittrail.dto.audit_dto import AuditLogFilterDTO


class TestAuditPolicy:
    """Tests für AuditPolicy."""

    @pytest.fixture
    def policy(self):
        """Policy-Instanz."""
        return AuditPolicy()

    # ===== can_read_logs() Tests =====

    def test_system_user_can_read_all(self, policy):
        """System-User (ID=0) hat vollen Zugriff."""
        assert policy.can_read_logs(0, None) is True
        assert policy.can_read_logs(0, AuditLogFilterDTO(user_id=99)) is True

    def test_admin_can_read_all(self, policy):
        """Admin (ID=1) hat vollen Zugriff."""
        assert policy.can_read_logs(1, None) is True
        assert policy.can_read_logs(1, AuditLogFilterDTO(user_id=99)) is True

    def test_qmb_can_read_all(self, policy):
        """QMB (ID=2) hat vollen Zugriff."""
        assert policy.can_read_logs(2, None) is True
        assert policy.can_read_logs(2, AuditLogFilterDTO(user_id=99)) is True

    def test_normal_user_can_read_own_logs(self, policy):
        """Normaler User kann eigene Logs lesen."""
        assert policy.can_read_logs(42, AuditLogFilterDTO(user_id=42)) is True

    def test_normal_user_cannot_read_other_logs(self, policy):
        """Normaler User kann fremde Logs NICHT lesen."""
        assert policy.can_read_logs(42, AuditLogFilterDTO(user_id=99)) is False

    def test_normal_user_cannot_read_without_filter(self, policy):
        """Normaler User kann ohne Filter NICHT alle Logs lesen."""
        assert policy.can_read_logs(42, None) is False
        assert policy.can_read_logs(42, AuditLogFilterDTO()) is False

    # ===== can_export_logs() Tests =====

    def test_system_user_can_export(self, policy):
        """System-User kann exportieren."""
        assert policy.can_export_logs(0) is True

    def test_admin_can_export(self, policy):
        """Admin kann exportieren."""
        assert policy.can_export_logs(1) is True

    def test_qmb_can_export(self, policy):
        """QMB kann exportieren."""
        assert policy.can_export_logs(2) is True

    def test_normal_user_cannot_export(self, policy):
        """Normaler User kann NICHT exportieren."""
        assert policy.can_export_logs(42) is False
