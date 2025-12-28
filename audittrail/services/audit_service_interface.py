"""
AuditTrail Service Interface

Definiert den Contract für das AuditTrail-Modul, das Compliance-konforme
Protokollierung und strukturiertes Application Logging vereint.

Design Principles:
- Wer/Wann/Wo/Was-Pattern verbindlich
- Feature-spezifische Konfiguration via meta.json
- Log-Levels + Audit-Severity parallel
- Erweiterbar für externe Sinks

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from audittrail.dto.audit_dto import AuditLogDTO, CreateAuditLogDTO, AuditLogFilterDTO
from audittrail.enum.audit_enum import LogLevel, AuditSeverity


class AuditServiceInterface(ABC):
    """
    Interface für AuditTrail-Service.

    Vereint Compliance-Audit und Application Logging in einem zentralen Service.
    Jedes Feature kann über diesen Service strukturierte Logs erstellen,
    die sowohl für Debugging als auch für regulatorische Nachweise verwendet werden.

    Key Features:
    - Wer/Wann/Wo/Was-Pattern für alle Logs
    - Feature-spezifische Konfiguration (meta.json)
    - Rollen-basierte Zugriffskontrolle (via Policy)
    - Export-Funktionen (JSON, CSV)
    - Auto-Cleanup nach Retention-Period
    """

    @abstractmethod
    def log(
        self,
        user_id: int,
        action: str,
        feature: str,
        log_level: LogLevel = LogLevel.INFO,
        severity: AuditSeverity = AuditSeverity.INFO,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        module: Optional[str] = None,
        function: Optional[str] = None
    ) -> int:
        """
        Zentrale Log-Methode (Audit + Application Logging).

        Args:
            user_id: ID des Benutzers (wer)
            action: Aktionstyp (was) - z.B. "LOGIN", "CREATE_DOCUMENT"
            feature: Feature-Name (wo) - z.B. "authenticator", "documentlifecycle"
            log_level: Log-Level für Entwickler (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            severity: Audit-Severity für Compliance (INFO, WARNING, CRITICAL)
            details: Zusätzliche Informationen als dict (z.B. {"document_id": 123})
            ip_address: IP-Adresse des Clients (optional)
            session_id: Session-ID (optional, falls vorhanden)
            module: Python-Modul (optional, z.B. "services.workflow_service")
            function: Funktionsname (optional, z.B. "start_workflow")

        Returns:
            int: ID des erstellten Log-Eintrags

        Raises:
            AuditException: Bei allgemeinem Fehler

        Example:
            >>> audit.log(
            ...     user_id=42,
            ...     action="START_WORKFLOW",
            ...     feature="documentlifecycle",
            ...     log_level=LogLevel.INFO,
            ...     severity=AuditSeverity.INFO,
            ...     details={"document_id": 123, "workflow_type": "review"}
            ... )
            1234
        """
        pass

    @abstractmethod
    def get_logs(self, filters: AuditLogFilterDTO) -> List[AuditLogDTO]:
        """
        Logs mit erweiterten Filtern abrufen.

        Args:
            filters: Filter-Kriterien (user_id, feature, action, log_level, etc.)

        Returns:
            Liste von AuditLogDTO (sortiert nach timestamp DESC)

        Raises:
            AuditAccessDeniedException: Wenn User keine Berechtigung hat

        Example:
            >>> filters = AuditLogFilterDTO(
            ...     feature="authenticator",
            ...     log_level="ERROR",
            ...     start_date=datetime(2025, 1, 1)
            ... )
            >>> logs = audit.get_logs(filters)
        """
        pass

    @abstractmethod
    def get_user_logs(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLogDTO]:
        """
        User-spezifische Logs abrufen.

        Args:
            user_id: ID des Benutzers
            start_date: Optional - Logs ab diesem Datum
            end_date: Optional - Logs bis zu diesem Datum

        Returns:
            Liste von AuditLogDTO

        Raises:
            AuditAccessDeniedException: Wenn User keine Berechtigung hat
                (User darf nur eigene Logs sehen, außer Admin/QMB)
        """
        pass

    @abstractmethod
    def get_feature_logs(
        self,
        feature: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLogDTO]:
        """
        Feature-spezifische Logs abrufen.

        Args:
            feature: Feature-Name (z.B. "documentlifecycle")
            start_date: Optional - Logs ab diesem Datum
            end_date: Optional - Logs bis zu diesem Datum

        Returns:
            Liste von AuditLogDTO

        Raises:
            AuditAccessDeniedException: Wenn User keine Berechtigung hat
                (nur Admin/QMB dürfen alle Features sehen)
        """
        pass

    @abstractmethod
    def search_logs(
        self,
        query: str,
        filters: Optional[AuditLogFilterDTO] = None
    ) -> List[AuditLogDTO]:
        """
        Volltext-Suche in Logs (durchsucht 'details' JSON).

        Args:
            query: Suchbegriff (z.B. "document_id:123" oder "error")
            filters: Optionale zusätzliche Filter

        Returns:
            Liste von AuditLogDTO

        Raises:
            AuditAccessDeniedException: Wenn User keine Berechtigung hat

        Example:
            >>> logs = audit.search_logs(
            ...     query="workflow",
            ...     filters=AuditLogFilterDTO(feature="documentlifecycle")
            ... )
        """
        pass

    @abstractmethod
    def export_logs(
        self,
        filters: AuditLogFilterDTO,
        format: str = "json"
    ) -> str:
        """
        Logs exportieren (json, csv).

        Args:
            filters: Filter-Kriterien
            format: Exportformat ("json" oder "csv")

        Returns:
            Exportierte Daten als String

        Raises:
            AuditAccessDeniedException: Wenn User keine Export-Berechtigung hat
                (nur Admin/QMB dürfen exportieren)
            ValueError: Wenn format ungültig ist

        Example:
            >>> filters = AuditLogFilterDTO(feature="authenticator")
            >>> csv_data = audit.export_logs(filters, format="csv")
        """
        pass

    @abstractmethod
    def delete_old_logs(self, feature: Optional[str] = None) -> int:
        """
        Alte Logs löschen (respektiert retention_days aus meta.json).

        Args:
            feature: Optional - nur Logs dieses Features löschen

        Returns:
            Anzahl gelöschter Logs

        Note:
            - Global: Löscht alle Logs älter als globaler retention_days
            - Feature-spezifisch: Nutzt retention_days aus meta.json des Features
            - Beispiel: documentlifecycle.meta.json → retention_days: 2555

        Example:
            >>> deleted_count = audit.delete_old_logs(feature="authenticator")
            >>> print(f"{deleted_count} Logs gelöscht")
        """
        pass

    @abstractmethod
    def set_min_log_level(
        self,
        level: LogLevel,
        feature: Optional[str] = None
    ) -> None:
        """
        Minimalen Log-Level setzen (global oder feature-spezifisch).

        Args:
            level: Neuer Min-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            feature: Optional - nur für dieses Feature (überschreibt global)

        Note:
            - Logs unter diesem Level werden nicht gespeichert
            - Production: Empfohlen INFO oder WARNING
            - Development: DEBUG für detaillierte Logs

        Example:
            >>> # Global: Nur WARNING+ loggen
            >>> audit.set_min_log_level(LogLevel.WARNING)
            >>>
            >>> # Feature-spezifisch: documentlifecycle DEBUG, Rest WARNING
            >>> audit.set_min_log_level(LogLevel.DEBUG, feature="documentlifecycle")
        """
        pass

    @abstractmethod
    def get_feature_audit_config(self, feature: str) -> Dict:
        """
        Audit-Konfiguration eines Features abrufen (aus meta.json).

        Args:
            feature: Feature-Name (z.B. "documentlifecycle")

        Returns:
            Dict mit Audit-Config:
                - must_audit (bool)
                - min_log_level (str)
                - critical_actions (List[str])
                - retention_days (int)

        Raises:
            FeatureNotFoundException: Wenn Feature nicht existiert

        Example:
            >>> config = audit.get_feature_audit_config("documentlifecycle")
            >>> print(config["retention_days"])  # 2555
        """
        pass
