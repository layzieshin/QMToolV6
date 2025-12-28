"""
AuditTrail Service Implementation

Zentrale Implementierung des AuditTrail-Moduls.
Vereint Compliance-Audit und Application Logging.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import json

from audittrail.services.audit_service_interface import AuditServiceInterface
from audittrail.dto.audit_dto import AuditLogDTO, CreateAuditLogDTO, AuditLogFilterDTO
from audittrail.enum.audit_enum import LogLevel, AuditSeverity, AuditActionType
from audittrail.exceptions.audit_exceptions import (
    AuditAccessDeniedException,
    FeatureNotFoundException,
    InvalidAuditLogException,
    ExportFormatException,
)


class AuditService(AuditServiceInterface):
    """
    Implementierung des AuditTrail-Service.

    Verwaltet alle Audit-Logs zentral und bietet strukturiertes Application Logging.
    """

    def __init__(self, repository, policy, configurator):
        """
        Initialisiert den AuditService.

        Args:
            repository: AuditRepository-Instanz
            policy: AuditPolicy-Instanz
            configurator: Configurator-Instanz (für meta.json)
        """
        self._repository = repository
        self._policy = policy
        self._configurator = configurator

        # ===== Min-Log-Level Config =====
        # globales Minimum, falls nichts Spezifisches gesetzt ist
        self._min_log_level_global: LogLevel = LogLevel.INFO
        # feature-spezifische Overrides
        self._min_log_level_per_feature: Dict[str, LogLevel] = {}

        # ===== Retention Config =====
        # globale Default-Retention (in Tagen)
        self._global_retention_days: int = 365
        # optionale feature-spezifische Retention-Werte (Cache)
        self._retention_days: Dict[str, int] = {}

    # ===== Public API =====

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
        function: Optional[str] = None,
    ) -> int:
        """Zentrale Log-Methode."""
        # 1. Min-Log-Level prüfen
        if not self._should_log(feature, log_level):
            return -1

        # 2. DTO bauen
        log_dto = CreateAuditLogDTO(
            user_id=user_id,
            feature=feature,
            action=action,
            log_level=log_level.value,
            severity=severity.value,
            module=module,
            function=function,
            details=details or {},
            ip_address=ip_address,
            session_id=session_id,
        )

        # 3. Username auflösen
        log_dto.username = self._resolve_username(user_id)

        # 4. Validieren
        try:
            log_dto.validate()
        except ValueError as e:
            raise InvalidAuditLogException(str(e))

        # 5. Speichern
        log_id = self._repository.create(log_dto)

        # 6. CRITICAL behandeln
        if severity == AuditSeverity.CRITICAL:
            self._handle_critical_log(log_dto, log_id)

        return log_id

    def get_logs(self, filters: AuditLogFilterDTO) -> List[AuditLogDTO]:
        """Logs mit Filtern abrufen."""
        current_user_id = self._get_current_user_id()
        if not self._policy.can_read_logs(current_user_id, filters):
            raise AuditAccessDeniedException(user_id=current_user_id)
        return self._repository.find_by_filters(filters)

    def get_user_logs(self, user_id: int) -> List[AuditLogDTO]:
        """Alle Logs für einen bestimmten User abrufen."""
        current_user_id = self._get_current_user_id()
        filters = AuditLogFilterDTO(user_id=user_id)
        if not self._policy.can_read_logs(current_user_id, filters):
            raise AuditAccessDeniedException(user_id=current_user_id)
        return self._repository.find_by_filters(filters)

    def get_feature_logs(self, feature: str) -> List[AuditLogDTO]:
        """Alle Logs für ein bestimmtes Feature abrufen."""
        current_user_id = self._get_current_user_id()
        filters = AuditLogFilterDTO(feature=feature)
        if not self._policy.can_read_logs(current_user_id, filters):
            raise AuditAccessDeniedException(user_id=current_user_id)
        return self._repository.find_by_filters(filters)

    def search_logs(self, keyword: str) -> List[AuditLogDTO]:
        """Volltextsuche über Logs."""
        current_user_id = self._get_current_user_id()
        # Zugriff auf alle Logs prüfen (Filter leer)
        filters = AuditLogFilterDTO()
        if not self._policy.can_read_logs(current_user_id, filters):
            raise AuditAccessDeniedException(user_id=current_user_id)
        return self._repository.search(keyword, filters)

    def export_logs(
        self,
        filters: AuditLogFilterDTO,
        format: str = "json",
    ) -> str:
        """Exportiert Logs als JSON oder CSV."""
        current_user_id = self._get_current_user_id()
        if not self._policy.can_read_logs(current_user_id, filters):
            raise AuditAccessDeniedException(user_id=current_user_id)

        logs = self._repository.find_by_filters(filters)

        format_lower = format.lower()
        if format_lower == "json":
            return self._export_json(logs)
        if format_lower == "csv":
            return self._export_csv(logs)

        raise ExportFormatException(format=format)

    def delete_old_logs(
        self,
        feature: Optional[str] = None,
        retention_days: Optional[int] = None,
    ) -> int:
        """
        Löscht alte Logs entsprechend Retention-Einstellungen.

        retention_days:
        \- wenn gesetzt: expliziter Wert
        \- sonst: feature-spezifisch oder global
        """
        if retention_days is not None:
            days = retention_days
        elif feature:
            days = self._get_feature_retention_days(feature)
        else:
            days = self._get_global_retention_days()

        cutoff_date = datetime.now() - timedelta(days=days)
        deleted = self._repository.delete_before(cutoff_date, feature)

        if deleted > 0:
            # systemischer Log über Löschvorgang
            self.log(
                user_id=0,
                action="DELETE_OLD_LOGS",
                feature="audittrail",
                log_level=LogLevel.INFO,
                severity=AuditSeverity.INFO,
                details={
                    "deleted_count": deleted,
                    "feature": feature,
                    "retention_days": days,
                    "cutoff_date": cutoff_date.isoformat(),
                },
            )

        return deleted

    def set_min_log_level(
        self,
        log_level: LogLevel,
        feature: Optional[str] = None,
    ) -> None:
        """
        Setzt das minimale LogLevel global oder für ein bestimmtes Feature.
        """
        if feature:
            self._min_log_level_per_feature[feature] = log_level
        else:
            self._min_log_level_global = log_level

    def get_feature_audit_config(self, feature: str) -> Dict:
        """Audit-Config aus meta.json laden."""
        try:
            meta = self._configurator.get_feature_meta(feature)
        except FileNotFoundError:
            raise FeatureNotFoundException(feature=feature)
        except Exception as e:
            # generische Fehler als FeatureNotFound maskieren
            raise FeatureNotFoundException(feature=feature) from e

        audit_cfg = meta.get("audit", {})
        must_audit = bool(audit_cfg.get("must_audit", False))
        min_log_level = str(audit_cfg.get("min_log_level", "INFO"))
        critical_actions = list(audit_cfg.get("critical_actions", []))

        return {
            "must_audit": must_audit,
            "min_log_level": min_log_level,
            "critical_actions": critical_actions,
        }

    # ===== Private Helper Methods =====

    def _should_log(self, feature: str, log_level: LogLevel) -> bool:
        """Prüft, ob Log gespeichert werden soll (basierend auf Min-Log-Level)."""
        feature_min = self._min_log_level_per_feature.get(feature)
        effective_min = feature_min if feature_min is not None else self._min_log_level_global
        return log_level.value >= effective_min.value

    def _resolve_username(self, user_id: int) -> str:
        """Fallback-Username\-Resolution."""
        return f"user_{user_id}"

    def _get_current_user_id(self) -> int:
        """Fallback für aktuellen User (noch keine Auth-Integration)."""
        return 0

    def _handle_critical_log(self, log_dto: CreateAuditLogDTO, log_id: int) -> None:
        """
        Behandelt CRITICAL-Logs (z\.B. Webhook, Mail).
        Aktuell Platzhalter.
        """
        pass

    def _get_feature_retention_days(self, feature: str) -> int:
        """
        Holt retention_days aus Feature-Descriptor (meta.json) oder Cache
        bzw. fällt auf globalen Default zurück.
        """
        if feature in self._retention_days:
            return self._retention_days[feature]

        try:
            meta = self._configurator.get_feature_meta(feature)
            days = int(meta.get("audit", {}).get("retention_days", self._global_retention_days))
        except Exception:
            days = self._global_retention_days

        self._retention_days[feature] = days
        return days

    def _get_global_retention_days(self) -> int:
        """
        Holt globale retention_days aus System-Config oder nutzt Default.
        """
        # TODO: Optional über Configurator laden
        return self._global_retention_days

    def _export_json(self, logs: List[AuditLogDTO]) -> str:
        """Exportiert Logs als JSON."""
        data = [log.to_dict() for log in logs]
        return json.dumps(data, indent=2, default=str)

    def _export_csv(self, logs: List[AuditLogDTO]) -> str:
        """Exportiert Logs als CSV."""
        header = "id,timestamp,user_id,username,feature,action,log_level,severity"
        if not logs:
            return header + "\n"

        lines = [header]
        for log in logs:
            lines.append(
                f"{log.id},"
                f"{log.timestamp.isoformat()},"
                f"{log.user_id},"
                f"{log.username},"
                f"{log.feature},"
                f"{log.action},"
                f"{log.log_level},"
                f"{log.severity}"
            )
        return "\n".join(lines)
