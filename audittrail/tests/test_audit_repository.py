"""
Unit Tests für AuditRepository

Testet Datenbankzugriff:
- CRUD-Operationen
- SQL-Injection-Sicherheit
- Filter-Abfragen

Author: QMToolV6 Development Team
Version: 1.0.0
"""
import pytest
from datetime import datetime, timedelta

from audittrail.dto.audit_dto import CreateAuditLogDTO, AuditLogFilterDTO
from audittrail.enum.audit_enum import LogLevel, AuditSeverity


class TestAuditRepository:
    """Tests für AuditRepository."""

    def test_create_log(self, audit_repository, sample_log_dto):
        """Log-Eintrag erstellen."""
        log_id = audit_repository.create(sample_log_dto)

        assert log_id > 0

    def test_find_by_filters_user_id(self, audit_repository, sample_log_dto):
        """Logs nach user_id filtern."""
        # Log erstellen
        audit_repository.create(sample_log_dto)

        # Abfragen
        filters = AuditLogFilterDTO(user_id=42)
        logs = audit_repository.find_by_filters(filters)

        assert len(logs) == 1
        assert logs[0].user_id == 42

    def test_find_by_filters_feature(self, audit_repository, sample_log_dto):
        """Logs nach feature filtern."""
        audit_repository.create(sample_log_dto)

        filters = AuditLogFilterDTO(feature="auth")
        logs = audit_repository.find_by_filters(filters)

        assert len(logs) == 1
        assert logs[0].feature == "auth"

    def test_find_by_filters_date_range(self, audit_repository, sample_log_dto):
        """Logs nach Zeitraum filtern."""
        audit_repository.create(sample_log_dto)

        filters = AuditLogFilterDTO(
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now() + timedelta(hours=1)
        )
        logs = audit_repository.find_by_filters(filters)

        assert len(logs) == 1

    def test_find_by_filters_empty_result(self, audit_repository):
        """Keine Logs gefunden."""
        filters = AuditLogFilterDTO(user_id=999)
        logs = audit_repository.find_by_filters(filters)

        assert len(logs) == 0

    def test_search_in_details(self, audit_repository):
        """Volltext-Suche in Details."""
        # Log mit spezifischem Detail erstellen
        log_dto = CreateAuditLogDTO(
            user_id=42,
            feature="auth",
            action="TEST",
            details={"error_code": "AUTH_FAILED"}
        )
        audit_repository.create(log_dto)

        # Suchen
        logs = audit_repository.search("AUTH_FAILED")

        assert len(logs) == 1
        assert "AUTH_FAILED" in str(logs[0].details)

    def test_delete_before(self, audit_repository, sample_log_dto):
        """Alte Logs löschen."""
        # Log erstellen
        audit_repository.create(sample_log_dto)

        # Löschen (in Zukunft → nichts gelöscht)
        cutoff = datetime.now() + timedelta(days=1)
        deleted = audit_repository.delete_before(cutoff)

        assert deleted == 1

    def test_sql_injection_protection(self, audit_repository):
        """SQL-Injection-Sicherheit prüfen."""
        # Böswilliger Input
        filters = AuditLogFilterDTO(feature="'; DROP TABLE audit_logs; --")

        # Sollte nicht crashen
        logs = audit_repository.find_by_filters(filters)

        assert len(logs) == 0  # Keine Logs gefunden (nicht gedropt!)
