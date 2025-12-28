"""
AuditTrail Service Implementation

Zentrale Implementierung des AuditTrail-Moduls.
Vereint Compliance-Audit und Application Logging.

Author: QMToolV6 Development Team
Version: 1.1.0
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import json

from audittrail.services.audit_service_interface import AuditServiceInterface
from audittrail.dto.audit_dto import AuditLogDTO, CreateAuditLogDTO, AuditLogFilterDTO
from audittrail.enum.audit_enum import LogLevel, AuditSeverity, AuditActionType
from audittrail. exceptions.audit_exceptions import (
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
            configurator:  Configurator-Instanz (für meta.json)
        """
        self._repository = repository
        self._policy = policy
        self._configurator = configurator

        # ===== Min-Log-Level Config =====
        # globales Minimum, falls nichts Spezifisches gesetzt ist
        self._min_log_level_global:  LogLevel = LogLevel.INFO
        # feature-spezifische Overrides
        self._min_log_level_per_feature: Dict[str, LogLevel] = {}

        # ===== Retention Config =====
        # globale Default-Retention (in Tagen)
        self._global_retention_days: int = 365
        # optionale feature-spezifische Retention-Werte (Cache)
        self._retention_days:  Dict[str, int] = {}

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
            log_level=log_level. value,
            severity=severity. value,
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
            raise InvalidAuditLogException(str(e), log_dto=log_dto.__dict__)

        # 5. Speichern
        log_id = self._repository.create(log_dto)

        # 6. CRITICAL behandeln
        if severity == AuditSeverity. CRITICAL:
            self._handle_critical_log(log_dto, log_id)

        return log_id

    def get_logs(self, filters: AuditLogFilterDTO) -> List[AuditLogDTO]:
        """Logs mit Filtern abrufen."""
        current_user_id = self._get_current_user_id()
        if not self._policy.can_read_logs(current_user_id, filters):
            raise AuditAccessDeniedException(
                f"User {current_user_id} hat keine Berechtigung zum Lesen der Logs",
                user_id=current_user_id,
                filters=str(filters)
            )
        return self._repository.find_by_filters(filters)

    def get_user_logs(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date:  Optional[datetime] = None
    ) -> List[AuditLogDTO]:
        """Alle Logs für einen bestimmten User abrufen."""
        current_user_id = self._get_current_user_id()
        filters = AuditLogFilterDTO(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        if not self._policy.can_read_logs(current_user_id, filters):
            raise AuditAccessDeniedException(
                f"User {current_user_id} hat keine Berechtigung zum Lesen von User {user_id} Logs",
                user_id=current_user_id,
                filters=str(filters)
            )
        return self._repository.find_by_filters(filters)

    def get_feature_logs(
        self,
        feature: str,
        start_date: Optional[datetime] = None,
        end_date:  Optional[datetime] = None
    ) -> List[AuditLogDTO]:
        """Alle Logs für ein bestimmtes Feature abrufen."""
        current_user_id = self._get_current_user_id()
        filters = AuditLogFilterDTO(
            feature=feature,
            start_date=start_date,
            end_date=end_date
        )
        if not self._policy.can_read_logs(current_user_id, filters):
            raise AuditAccessDeniedException(
                f"User {current_user_id} hat keine Berechtigung zum Lesen von Feature {feature} Logs",
                user_id=current_user_id,
                filters=str(filters)
            )
        return self._repository.find_by_filters(filters)

    def search_logs(
        self,
        query: str,
        filters: Optional[AuditLogFilterDTO] = None
    ) -> List[AuditLogDTO]:
        """Volltextsuche über Logs."""
        current_user_id = self._get_current_user_id()
        # Zugriff auf alle Logs prüfen (Filter leer falls nicht gesetzt)
        search_filters = filters if filters is not None else AuditLogFilterDTO()
        if not self._policy.can_read_logs(current_user_id, search_filters):
            raise AuditAccessDeniedException(
                f"User {current_user_id} hat keine Berechtigung zur Suche",
                user_id=current_user_id,
                filters=str(search_filters)
            )
        return self._repository. search(query, search_filters)

    def export_logs(
        self,
        filters: AuditLogFilterDTO,
        format: str = "json",
    ) -> str:
        """Exportiert Logs als JSON oder CSV."""
        current_user_id = self._get_current_user_id()

        # Prüfe Export-Berechtigung
        if not self._policy.can_export_logs(current_user_id):
            raise AuditAccessDeniedException(
                f"User {current_user_id} hat keine Export-Berechtigung",
                user_id=current_user_id
            )

        # Prüfe Lese-Berechtigung für gefilterte Logs
        if not self._policy.can_read_logs(current_user_id, filters):
            raise AuditAccessDeniedException(
                f"User {current_user_id} hat keine Berechtigung zum Lesen der zu exportierenden Logs",
                user_id=current_user_id,
                filters=str(filters)
            )

        logs = self._repository.find_by_filters(filters)

        format_lower = format.lower()
        if format_lower == "json":
            return self._export_json(logs)
        elif format_lower == "csv":
            return self._export_csv(logs)
        else:
            raise ExportFormatException(
                f"Ungültiges Format: {format}. Erlaubt: json, csv",
                format=format
            )

    def delete_old_logs(
        self,
        feature: Optional[str] = None,
        retention_days: Optional[int] = None,
    ) -> int:
        """
        Löscht alte Logs entsprechend Retention-Einstellungen.

        retention_days:
        - wenn gesetzt: expliziter Wert
        - sonst: feature-spezifisch oder global
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
            self. log(
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
        level: LogLevel,
        feature:  Optional[str] = None,
    ) -> None:
        """
        Setzt das minimale LogLevel global oder für ein bestimmtes Feature.
        """
        if feature:
            self._min_log_level_per_feature[feature] = level
        else:
            self._min_log_level_global = level

    def get_feature_audit_config(self, feature: str) -> Dict:
        """Audit-Config aus meta.json laden."""
        try:
            meta = self._configurator.get_feature_meta(feature)
        except FileNotFoundError as e:
            raise FeatureNotFoundException(
                f"Feature '{feature}' nicht gefunden",
                feature=feature
            ) from e
        except Exception as e:
            # generische Fehler als FeatureNotFound maskieren
            raise FeatureNotFoundException(
                f"Fehler beim Laden von Feature '{feature}': {str(e)}",
                feature=feature
            ) from e

        audit_cfg = meta.get("audit", {})
        must_audit = bool(audit_cfg.get("must_audit", False))
        min_log_level = str(audit_cfg.get("min_log_level", "INFO"))
        critical_actions = list(audit_cfg.get("critical_actions", []))
        retention_days = int(audit_cfg.get("retention_days", self._global_retention_days))

        return {
            "must_audit":  must_audit,
            "min_log_level": min_log_level,
            "critical_actions": critical_actions,
            "retention_days": retention_days,
        }

    # ===== Private Helper Methods =====

    def _should_log(self, feature: str, log_level: LogLevel) -> bool:
        """
        Prüft, ob Log gespeichert werden soll (basierend auf Min-Log-Level).

        FIX: Korrekter Enum-Vergleich über _compare_log_levels
        """
        feature_min = self._min_log_level_per_feature.get(feature)
        effective_min = feature_min if feature_min is not None else self._min_log_level_global
        return self._compare_log_levels(log_level, effective_min) >= 0

    def _compare_log_levels(self, level1: LogLevel, level2: LogLevel) -> int:
        """
        Vergleicht zwei LogLevels.

        Returns:
            -1 wenn level1 < level2
             0 wenn level1 == level2
             1 wenn level1 > level2
        """
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO:  1,
            LogLevel. WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }

        order1 = level_order.get(level1, 0)
        order2 = level_order.get(level2, 0)

        if order1 < order2:
            return -1
        elif order1 > order2:
            return 1
        else:
            return 0

    def _resolve_username(self, user_id:  int) -> str:
        """Fallback-Username-Resolution."""
        if user_id == 0:
            return "SYSTEM"
        return f"user_{user_id}"

    def _get_current_user_id(self) -> int:
        """Fallback für aktuellen User (noch keine Auth-Integration)."""
        return 0

    def _handle_critical_log(self, log_dto: CreateAuditLogDTO, log_id: int) -> None:
        """
        Behandelt CRITICAL-Logs (z.B. Webhook, Mail).
        Aktuell Platzhalter.
        """
        # TODO:  Implementierung für Benachrichtigungen
        pass

    def _get_feature_retention_days(self, feature:  str) -> int:
        """
        Holt retention_days aus Feature-Descriptor (meta.json) oder Cache
        bzw. fällt auf globalen Default zurück.
        """
        if feature in self._retention_days:
            return self._retention_days[feature]

        try:
            config = self.get_feature_audit_config(feature)
            days = int(config.get("retention_days", self._global_retention_days))
        except FeatureNotFoundException:
            days = self._global_retention_days
        except (ValueError, TypeError):
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

    def _export_csv(self, logs:  List[AuditLogDTO]) -> str:
        """Exportiert Logs als CSV."""
        header = "id,timestamp,user_id,username,feature,action,log_level,severity,ip_address,session_id,module,function"
        if not logs:
            return header + "\n"

        lines = [header]
        for log in logs:
            # Escape CSV-Werte
            lines.append(
                f"{log.id},"
                f"{log.timestamp. isoformat()},"
                f"{log.user_id},"
                f'"{self._escape_csv(log.username)}",'
                f'"{self._escape_csv(log.feature)}",'
                f'"{self._escape_csv(log.action)}",'
                f"{log.log_level},"
                f"{log.severity},"
                f'"{self._escape_csv(log.ip_address or "")}",'
                f'"{self._escape_csv(log.session_id or "")}",'
                f'"{self._escape_csv(log.module or "")}",'
                f'"{self._escape_csv(log.function or "")}"'
            )
        return "\n".join(lines)

    def _escape_csv(self, value: str) -> str:
        """Escaped CSV-Werte (Anführungszeichen verdoppeln)."""
        if value is None:
            return ""
        return value.replace('"', '""')