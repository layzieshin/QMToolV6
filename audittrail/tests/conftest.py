"""
Shared Test Fixtures für AuditTrail

Stellt wiederverwendbare Fixtures für alle Tests bereit:
- In-Memory SQLite DB
- Mock-Instanzen (Repository, Policy, Configurator)
- Sample-DTOs

Author: QMToolV6 Development Team
Version: 1.0.0
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock

from audittrail.repository.audit_repository import AuditRepository
from audittrail.services.policy.audit_policy import AuditPolicy
from audittrail.services.audit_service import AuditService
from audittrail.dto.audit_dto import CreateAuditLogDTO, AuditLogFilterDTO
from audittrail.enum.audit_enum import LogLevel, AuditSeverity, AuditActionType


@pytest.fixture
def temp_db_path():
    """Erstellt temporäre SQLite-Datei für Tests."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()
    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def audit_repository():
    """AuditRepository mit In-Memory DB."""
    # ✅ ":memory:" → Keine Datei, kein File Lock
    repo = AuditRepository(":memory:")
    yield repo

    # Connection schließen
    if hasattr(repo, '_conn'):
        repo._conn.close()


@pytest.fixture
def audit_policy():
    """AuditPolicy-Instanz."""
    return AuditPolicy()


@pytest.fixture
def mock_configurator():
    """Mock für Configurator (Feature-Descriptors)."""
    configurator = Mock()

    # Standard meta.json für "auth"
    configurator.get_feature_meta.return_value = {
        "audit": {
            "must_audit": True,
            "min_log_level": "INFO",
            "critical_actions": ["LOGIN_FAILED"],
            "retention_days": 365
        }
    }

    return configurator


@pytest.fixture
def audit_service(audit_repository, audit_policy, mock_configurator):
    """Vollständiger AuditService (mit echtem Repository)."""
    return AuditService(audit_repository, audit_policy, mock_configurator)


@pytest.fixture
def sample_log_dto():
    """Standard CreateAuditLogDTO für Tests."""
    return CreateAuditLogDTO(
        user_id=42,
        username="test_user",
        feature="auth",
        action="LOGIN",
        log_level=LogLevel.INFO.value,
        severity=AuditSeverity.INFO.value,
        ip_address="192.168.1.100",
        session_id="session_123",
        module="authentication",
        function="login_user",
        details={"success": True}
    )


@pytest.fixture
def sample_filter_dto():
    """Standard AuditLogFilterDTO für Tests."""
    return AuditLogFilterDTO(
        user_id=42,
        feature="auth",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now()
    )
