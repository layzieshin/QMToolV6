"""
Unit Tests für AuditTrail DTOs

Testet:
- CreateAuditLogDTO Validierung
- AuditLogFilterDTO SQL-Generierung
- Konvertierungen zwischen DTOs

Author: QMToolV6 Development Team
Version: 1.0.0
"""
import pytest
from datetime import datetime

from audittrail.dto.audit_dto import CreateAuditLogDTO, AuditLogDTO, AuditLogFilterDTO
from audittrail.enum.audit_enum import LogLevel, AuditSeverity
from audittrail.exceptions.audit_exceptions import InvalidAuditLogException


class TestCreateAuditLogDTO:
    """Tests für CreateAuditLogDTO."""

    def test_validate_success(self, sample_log_dto):
        """Gültige DTOs passieren Validierung."""
        # Sollte nicht werfen
        sample_log_dto.validate()

    def test_validate_missing_user_id(self):
        """user_id muss gesetzt sein."""
        dto = CreateAuditLogDTO(
            user_id=None,  # Invalid!
            feature="auth",
            action="TEST"
        )
        with pytest.raises(ValueError, match="user_id"):
            dto.validate()

    def test_validate_missing_feature(self):
        """feature muss gesetzt sein."""
        dto = CreateAuditLogDTO(
            user_id=42,
            feature="",  # Invalid!
            action="TEST"
        )
        with pytest.raises(ValueError, match="feature"):
            dto.validate()

    def test_validate_missing_action(self):
        """action muss gesetzt sein."""
        dto = CreateAuditLogDTO(
            user_id=42,
            feature="auth",
            action=""  # Invalid!
        )
        with pytest.raises(ValueError, match="action"):
            dto.validate()

    def test_to_audit_log_dto(self, sample_log_dto):
        """Konvertierung zu AuditLogDTO funktioniert."""
        audit_log = sample_log_dto.to_audit_log_dto(log_id=123)

        assert audit_log.id == 123
        assert audit_log.user_id == sample_log_dto.user_id
        assert audit_log.feature == sample_log_dto.feature
        assert audit_log.action == sample_log_dto.action


class TestAuditLogFilterDTO:
    """Tests für AuditLogFilterDTO."""

    def test_to_sql_conditions_all_filters(self):
        """SQL-Generierung mit allen Filtern."""
        filters = AuditLogFilterDTO(
            user_id=42,
            feature="auth",
            action="LOGIN",
            log_level="INFO",
            severity="WARNING",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        where_clause, params = filters.to_sql_conditions()

        assert "user_id = ?" in where_clause
        assert "feature = ?" in where_clause
        assert "action = ?" in where_clause
        assert "log_level = ?" in where_clause
        assert "severity = ?" in where_clause
        assert "timestamp >= ?" in where_clause
        assert "timestamp <= ?" in where_clause
        assert len(params) == 7

    def test_to_sql_conditions_no_filters(self):
        """SQL ohne Filter (nur 1=1)."""
        filters = AuditLogFilterDTO()

        where_clause, params = filters.to_sql_conditions()

        assert where_clause == "1=1"
        assert params == []

    def test_has_filters_true(self):
        """has_filters() erkennt gesetzte Filter."""
        filters = AuditLogFilterDTO(user_id=42)
        assert filters.has_filters() is True

    def test_has_filters_false(self):
        """has_filters() erkennt leere Filter."""
        filters = AuditLogFilterDTO()
        assert filters.has_filters() is False


class TestAuditLogDTO:
    """Tests für AuditLogDTO."""

    def test_to_dict(self):
        """to_dict() konvertiert korrekt."""
        dto = AuditLogDTO(
            id=123,
            timestamp=datetime(2024, 1, 1, 12, 0),
            user_id=42,
            username="test_user",
            feature="auth",
            action="LOGIN",
            log_level="INFO",
            severity="INFO",
            details={"success": True}
        )

        result = dto.to_dict()

        assert result["id"] == 123
        assert result["user_id"] == 42
        assert result["feature"] == "auth"
        assert result["details"]["success"] is True
