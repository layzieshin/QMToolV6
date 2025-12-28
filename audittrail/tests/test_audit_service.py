"""
Unit Tests für AuditService

Testet Business Logic:
- log() Methode (mit Min-Log-Level)
- get_logs() + Zugriffskontrolle
- export_logs()
- delete_old_logs()
- Exception-Handling

Author: QMToolV6 Development Team
Version: 1.1.0
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from audittrail.services. audit_service import AuditService
from audittrail.dto.audit_dto import CreateAuditLogDTO, AuditLogFilterDTO
from audittrail.enum.audit_enum import LogLevel, AuditSeverity, AuditActionType
from audittrail.exceptions.audit_exceptions import (
    AuditAccessDeniedException,
    FeatureNotFoundException,
    InvalidAuditLogException,
    ExportFormatException
)


class TestAuditService:
    """Tests für AuditService."""

    # ===== log() Tests =====

    def test_log_success(self, audit_service):
        """Erfolgreicher Log-Eintrag."""
        log_id = audit_service.log(
            user_id=42,
            action="LOGIN",
            feature="auth",
            log_level=LogLevel.INFO,
            severity=AuditSeverity. INFO
        )

        assert log_id > 0

    def test_log_below_min_level(self, audit_service):
        """Log unter min_log_level wird nicht gespeichert."""
        # Min-Level auf WARNING setzen
        audit_service. set_min_log_level(LogLevel.WARNING, feature="auth")

        # INFO-Log sollte nicht gespeichert werden
        log_id = audit_service.log(
            user_id=1,
            action="TEST",
            feature="auth",
            log_level=LogLevel. INFO
        )

        assert log_id == -1

    def test_log_invalid_dto_raises_exception(self, audit_service):
        """Ungültige DTOs werfen InvalidAuditLogException."""
        with pytest.raises((InvalidAuditLogException, ValueError)):
            audit_service.log(
                user_id=-1,  # Invalid!  (None wird durch Python selbst abgefangen)
                action="TEST",
                feature="auth"
            )

    def test_log_critical_triggers_handler(self, audit_service):
        """CRITICAL-Logs triggern _handle_critical_log()."""
        with patch.object(audit_service, '_handle_critical_log') as mock_handler:
            audit_service.log(
                user_id=42,
                action="SECURITY_BREACH",
                feature="auth",
                severity=AuditSeverity. CRITICAL
            )

            mock_handler.assert_called_once()

    # ===== get_logs() Tests =====

    def test_get_logs_success(self, audit_service):
        """Logs abrufen (mit Berechtigung)."""
        # Log erstellen
        audit_service.log(42, "TEST", "auth")

        # Abrufen (als System-User)
        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            filters = AuditLogFilterDTO(user_id=42)
            logs = audit_service. get_logs(filters)

            assert len(logs) == 1
            assert logs[0].user_id == 42

    def test_get_logs_access_denied(self, audit_service):
        """Zugriff verweigert für fremde Logs."""
        # Log von User 42 erstellen
        audit_service.log(42, "TEST", "auth")

        # User 99 versucht Zugriff
        with patch.object(audit_service, '_get_current_user_id', return_value=99):
            filters = AuditLogFilterDTO(user_id=42)

            with pytest.raises(AuditAccessDeniedException) as exc_info:
                audit_service.get_logs(filters)

            assert exc_info.value.user_id == 99

    # ===== get_user_logs() Tests =====

    def test_get_user_logs(self, audit_service):
        """User-spezifische Logs abrufen."""
        audit_service.log(42, "LOGIN", "auth")
        audit_service.log(42, "LOGOUT", "auth")

        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            logs = audit_service.get_user_logs(42)

            assert len(logs) == 2
            assert all(log.user_id == 42 for log in logs)

    # ===== get_feature_logs() Tests =====

    def test_get_feature_logs(self, audit_service):
        """Feature-spezifische Logs abrufen."""
        audit_service.log(42, "CREATE", "documents")
        audit_service.log(99, "UPDATE", "documents")

        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            logs = audit_service.get_feature_logs("documents")

            assert len(logs) == 2
            assert all(log.feature == "documents" for log in logs)

    # ===== search_logs() Tests =====

    def test_search_logs_success(self, audit_service):
        """Volltext-Suche in Logs."""
        audit_service.log(
            user_id=42,
            action="TEST",
            feature="auth",
            details={"error": "AUTH_FAILED"}
        )

        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            logs = audit_service.search_logs("AUTH_FAILED")

            assert len(logs) >= 1

    def test_search_logs_access_denied(self, audit_service):
        """Suche ohne Berechtigung verweigert."""
        with patch.object(audit_service, '_get_current_user_id', return_value=99):
            with pytest.raises(AuditAccessDeniedException):
                audit_service.search_logs("test")

    # ===== export_logs() Tests =====

    def test_export_logs_json(self, audit_service):
        """Export als JSON."""
        audit_service.log(42, "TEST", "auth")

        with patch. object(audit_service, '_get_current_user_id', return_value=0):
            filters = AuditLogFilterDTO()
            json_export = audit_service.export_logs(filters, format="json")

            assert isinstance(json_export, str)
            assert "TEST" in json_export

    def test_export_logs_csv(self, audit_service):
        """Export als CSV."""
        audit_service.log(42, "TEST", "auth")

        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            filters = AuditLogFilterDTO()
            csv_export = audit_service.export_logs(filters, format="csv")

            assert isinstance(csv_export, str)
            assert "timestamp" in csv_export  # CSV-Header

    def test_export_logs_invalid_format(self, audit_service):
        """Ungültiges Export-Format wirft Exception."""
        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            filters = AuditLogFilterDTO()

            with pytest.raises(ExportFormatException) as exc_info:
                audit_service.export_logs(filters, format="xml")

            assert exc_info.value.format == "xml"

    def test_export_logs_access_denied(self, audit_service):
        """Export ohne Berechtigung verweigert."""
        with patch.object(audit_service, '_get_current_user_id', return_value=99):
            filters = AuditLogFilterDTO()

            with pytest.raises(AuditAccessDeniedException):
                audit_service.export_logs(filters)

    # ===== delete_old_logs() Tests =====

    def test_delete_old_logs_global(self, audit_service, audit_repository):
        """Alte Logs löschen (global)."""
        # Log erstellen
        log_id = audit_service.log(1, "OLD_LOG", "auth")
        assert log_id > 0

        # Manuell altes Timestamp setzen (direkt in DB)
        old_timestamp = (datetime.now() - timedelta(days=400)).isoformat()
        audit_repository._conn.execute(
            "UPDATE audit_logs SET timestamp = ? WHERE id = ?",
            (old_timestamp, log_id)
        )
        audit_repository._conn.commit()

        # Löschen (365 Tage Retention)
        deleted = audit_service.delete_old_logs()

        assert deleted >= 1

    def test_delete_old_logs_feature(self, audit_service, audit_repository):
        """Alte Logs löschen (feature-spezifisch)."""
        # Logs erstellen
        log_id_auth = audit_service.log(1, "TEST", "auth")
        log_id_docs = audit_service.log(1, "TEST", "documents")

        # Auth-Log alt machen
        old_timestamp = (datetime.now() - timedelta(days=400)).isoformat()
        audit_repository._conn.execute(
            "UPDATE audit_logs SET timestamp = ? WHERE id = ?",
            (old_timestamp, log_id_auth)
        )
        audit_repository._conn.commit()

        # Nur auth löschen
        deleted = audit_service.delete_old_logs(feature="auth")

        assert deleted >= 1

        # Verifizieren: documents-Log noch da
        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            logs = audit_service.get_logs(AuditLogFilterDTO(feature="documents"))
            assert len(logs) == 1

    def test_delete_old_logs_custom_retention(self, audit_service, audit_repository):
        """Löschen mit expliziter Retention."""
        # Log erstellen
        log_id = audit_service.log(1, "TEST", "auth")

        # 10 Tage alt machen
        old_timestamp = (datetime.now() - timedelta(days=10)).isoformat()
        audit_repository._conn.execute(
            "UPDATE audit_logs SET timestamp = ? WHERE id = ?",
            (old_timestamp, log_id)
        )
        audit_repository._conn.commit()

        # Mit 7 Tagen Retention löschen
        deleted = audit_service.delete_old_logs(retention_days=7)

        assert deleted >= 1

    # ===== set_min_log_level() Tests =====

    def test_set_min_log_level_global(self, audit_service):
        """Globalen min_log_level setzen."""
        audit_service.set_min_log_level(LogLevel.WARNING)

        # DEBUG sollte nicht geloggt werden
        log_id = audit_service.log(42, "TEST", "auth", log_level=LogLevel.DEBUG)
        assert log_id == -1

        # WARNING sollte geloggt werden
        log_id = audit_service.log(42, "TEST", "auth", log_level=LogLevel. WARNING)
        assert log_id > 0

    def test_set_min_log_level_feature(self, audit_service):
        """Feature-spezifischen min_log_level setzen."""
        audit_service.set_min_log_level(LogLevel.ERROR, feature="auth")

        # INFO auf "auth" nicht geloggt
        log_id = audit_service.log(1, "TEST", "auth", log_level=LogLevel.INFO)
        assert log_id == -1

        # INFO auf "documents" geloggt (global = INFO)
        log_id = audit_service.log(1, "TEST", "documents", log_level=LogLevel.INFO)
        assert log_id > 0

    # ===== get_feature_audit_config() Tests =====

    def test_get_feature_audit_config_success(self, audit_service):
        """Feature-Config aus meta.json laden."""
        config = audit_service.get_feature_audit_config("auth")

        assert config["must_audit"] is True
        assert config["min_log_level"] == "INFO"
        assert "LOGIN_FAILED" in config["critical_actions"]

    def test_get_feature_audit_config_not_found(self, audit_service, mock_configurator):
        """Feature nicht gefunden wirft Exception."""
        mock_configurator.get_feature_meta.side_effect = FileNotFoundError()

        with pytest.raises(FeatureNotFoundException) as exc_info:
            audit_service.get_feature_audit_config("invalid_feature")

        assert exc_info.value.feature == "invalid_feature"

    # ===== Helper Methods Tests =====

    def test_resolve_username_fallback(self, audit_service):
        """Username-Resolution fällt auf user_{id} zurück."""
        username = audit_service._resolve_username(42)
        assert username == "user_42"

    def test_resolve_username_system(self, audit_service):
        """Username für System-User (ID=0)."""
        username = audit_service._resolve_username(0)
        assert username == "SYSTEM"

    def test_get_current_user_id_fallback(self, audit_service):
        """Current User ID fällt auf 0 (System) zurück."""
        user_id = audit_service._get_current_user_id()
        assert user_id == 0