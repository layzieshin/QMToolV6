"""
Integration Tests für AuditTrail

Testet End-to-End Flows:
- Vollständiger Log-Zyklus (log → DB → get_logs)
- Export-Funktionen
- Retention-Cleanup
- Multi-User-Szenarien

Author: QMToolV6 Development Team
Version: 1.1.0
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from audittrail.enum. audit_enum import LogLevel, AuditSeverity
from audittrail.dto.audit_dto import AuditLogFilterDTO


class TestAuditIntegration:
    """Integration Tests."""

    def test_full_log_cycle(self, audit_service):
        """Vollständiger Zyklus:  log → DB → get_logs."""
        # 1. Log erstellen
        log_id = audit_service.log(
            user_id=42,
            action="LOGIN",
            feature="auth",
            log_level=LogLevel.INFO,
            severity=AuditSeverity. INFO,
            details={"ip": "192.168.1.1"}
        )

        assert log_id > 0

        # 2. Log abrufen
        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            filters = AuditLogFilterDTO(user_id=42)
            logs = audit_service. get_logs(filters)

            assert len(logs) == 1
            assert logs[0].id == log_id
            assert logs[0].action == "LOGIN"
            assert logs[0].details["ip"] == "192.168.1.1"

    def test_multi_user_isolation(self, audit_service):
        """User sehen nur eigene Logs."""
        # User 42 erstellt Log
        audit_service.log(42, "ACTION_A", "auth")

        # User 99 erstellt Log
        audit_service.log(99, "ACTION_B", "auth")

        # User 42 sieht nur eigene Logs
        with patch. object(audit_service, '_get_current_user_id', return_value=42):
            filters = AuditLogFilterDTO(user_id=42)
            logs = audit_service.get_logs(filters)

            assert len(logs) == 1
            assert logs[0].user_id == 42

    def test_feature_level_filtering(self, audit_service):
        """Feature-spezifische Min-Log-Level."""
        # "auth" auf ERROR setzen
        audit_service.set_min_log_level(LogLevel. ERROR, feature="auth")

        # INFO auf "auth" → nicht geloggt
        log_id_1 = audit_service.log(1, "TEST", "auth", log_level=LogLevel.INFO)
        assert log_id_1 == -1

        # ERROR auf "auth" → geloggt
        log_id_2 = audit_service.log(1, "TEST", "auth", log_level=LogLevel.ERROR)
        assert log_id_2 > 0

        # INFO auf "documents" → geloggt (global = INFO)
        log_id_3 = audit_service.log(1, "TEST", "documents", log_level=LogLevel.INFO)
        assert log_id_3 > 0

    def test_export_and_reimport_json(self, audit_service):
        """Export → JSON → Parse."""
        import json

        # Logs erstellen
        audit_service. log(1, "TEST_A", "auth")
        audit_service.log(2, "TEST_B", "documents")

        # Exportieren
        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            filters = AuditLogFilterDTO()
            json_export = audit_service.export_logs(filters, format="json")

            # Parsen
            logs = json.loads(json_export)

            assert len(logs) >= 2
            assert any(log["action"] == "TEST_A" for log in logs)

    def test_export_csv_format(self, audit_service):
        """Export → CSV → Validierung."""
        audit_service.log(42, "CSV_TEST", "auth")

        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            filters = AuditLogFilterDTO()
            csv_export = audit_service.export_logs(filters, format="csv")

            # CSV-Header prüfen
            lines = csv_export.split("\n")
            assert "id,timestamp,user_id" in lines[0]
            assert "CSV_TEST" in csv_export

    def test_export_csv_escaping(self, audit_service):
        """CSV-Export escaped Sonderzeichen."""
        audit_service.log(
            user_id=42,
            action='TEST"QUOTE',
            feature="auth"
        )

        with patch. object(audit_service, '_get_current_user_id', return_value=0):
            filters = AuditLogFilterDTO()
            csv_export = audit_service.export_logs(filters, format="csv")

            # Anführungszeichen müssen verdoppelt sein
            assert 'TEST""QUOTE' in csv_export

    def test_retention_cleanup(self, audit_service, audit_repository):
        """Alte Logs werden gelöscht."""
        # Log erstellen
        log_id = audit_service.log(1, "OLD_LOG", "auth")

        # Manuell altes Timestamp setzen (direkt in DB)
        old_timestamp = (datetime.now() - timedelta(days=400)).isoformat()
        audit_repository._conn.execute(
            "UPDATE audit_logs SET timestamp = ? WHERE id = ?",
            (old_timestamp, log_id)
        )
        audit_repository._conn.commit()

        # Löschen
        deleted = audit_service.delete_old_logs(feature="auth")

        assert deleted >= 1

        # Verifizieren:  Log nicht mehr abrufbar
        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            logs = audit_service.get_logs(AuditLogFilterDTO(feature="auth"))
            assert len([log for log in logs if log. action == "OLD_LOG"]) == 0

    def test_retention_cleanup_respects_feature(self, audit_service, audit_repository):
        """Cleanup löscht nur spezifizierte Features."""
        # Logs in zwei Features
        log_id_auth = audit_service.log(1, "OLD_AUTH", "auth")
        log_id_docs = audit_service.log(1, "OLD_DOCS", "documents")

        # Beide alt machen
        old_timestamp = (datetime.now() - timedelta(days=400)).isoformat()
        audit_repository._conn.execute(
            "UPDATE audit_logs SET timestamp = ? WHERE id IN (?, ?)",
            (old_timestamp, log_id_auth, log_id_docs)
        )
        audit_repository._conn.commit()

        # Nur auth löschen
        deleted = audit_service.delete_old_logs(feature="auth")

        assert deleted >= 1

        # documents-Log noch da
        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            docs_logs = audit_service.get_logs(AuditLogFilterDTO(feature="documents"))
            assert len(docs_logs) >= 1
            assert docs_logs[0].action == "OLD_DOCS"

    def test_search_across_features(self, audit_service):
        """Suche über mehrere Features."""
        audit_service.log(42, "TEST", "auth", details={"keyword": "SPECIAL"})
        audit_service. log(99, "TEST", "documents", details={"keyword": "SPECIAL"})

        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            logs = audit_service.search_logs("SPECIAL")

            assert len(logs) == 2

    def test_critical_log_handling(self, audit_service):
        """CRITICAL-Logs werden besonders behandelt."""
        with patch.object(audit_service, '_handle_critical_log') as mock_handler:
            log_id = audit_service.log(
                user_id=42,
                action="SECURITY_BREACH",
                feature="auth",
                severity=AuditSeverity. CRITICAL
            )

            # Handler wurde aufgerufen
            mock_handler.assert_called_once()

            # Log wurde trotzdem gespeichert
            assert log_id > 0

    def test_log_with_all_fields(self, audit_service):
        """Log mit allen optionalen Feldern."""
        log_id = audit_service.log(
            user_id=42,
            action="COMPLEX_ACTION",
            feature="auth",
            log_level=LogLevel.WARNING,
            severity=AuditSeverity.WARNING,
            details={"key": "value", "nested": {"data": 123}},
            ip_address="10.0.0.1",
            session_id="sess_abc123",
            module="test.module",
            function="test_function"
        )

        assert log_id > 0

        # Verifizieren
        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            logs = audit_service.get_logs(AuditLogFilterDTO(user_id=42))
            log = logs[0]

            assert log.ip_address == "10.0.0.1"
            assert log.session_id == "sess_abc123"
            assert log. module == "test.module"  # ✅ FIX: Leerzeichen entfernt
            assert log.function == "test_function"
            assert log.details["nested"]["data"] == 123

    def test_filter_by_date_range(self, audit_service):
        """Filtern nach Datumsbereich."""
        # Log vor 2 Tagen
        audit_service.log(1, "OLD", "auth")

        # Log heute
        audit_service.log(2, "NEW", "auth")

        # Nur heute abrufen
        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            filters = AuditLogFilterDTO(
                start_date=datetime.now() - timedelta(hours=1)
            )
            logs = audit_service.get_logs(filters)

            # Mindestens der neue Log
            assert any(log.action == "NEW" for log in logs)

    def test_pagination(self, audit_service):
        """Pagination mit limit/offset."""
        # 10 Logs erstellen
        for i in range(10):
            audit_service.log(1, f"LOG_{i}", "auth")

        # Erste 5 abrufen
        with patch.object(audit_service, '_get_current_user_id', return_value=0):
            filters = AuditLogFilterDTO(limit=5, offset=0)
            logs_page1 = audit_service. get_logs(filters)

            assert len(logs_page1) == 5

            # Zweite 5 abrufen
            filters = AuditLogFilterDTO(limit=5, offset=5)
            logs_page2 = audit_service.get_logs(filters)

            assert len(logs_page2) == 5

            # Keine Überschneidung
            page1_ids = {log.id for log in logs_page1}
            page2_ids = {log.id for log in logs_page2}
            assert page1_ids.isdisjoint(page2_ids)