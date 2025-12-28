"""
AuditTrail Data Transfer Objects

Definiert alle DTOs für das AuditTrail-Modul:
- AuditLogDTO: Vollständiger Log-Eintrag (Lesen)
- CreateAuditLogDTO: Input für Log-Erstellung (Schreiben)
- AuditLogFilterDTO: Filter-Kriterien für Suche

Design Principles:
- Immutable (frozen dataclasses)
- Type-Safe (mit Type-Hints)
- Wer/Wann/Wo/Was-Pattern
- JSON-serializable

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict


@dataclass(frozen=True)
class AuditLogDTO:
    """
    Vollständiger Audit-Log-Eintrag (Lesen aus DB).

    Repräsentiert das Wer/Wann/Wo/Was-Pattern:
    - Wer: user_id, username, ip_address, session_id
    - Wann: timestamp
    - Wo: feature, module, function
    - Was: action, log_level, severity, details

    Immutable (frozen=True) → Garantiert unveränderliche Audit-Logs.
    """
    # ===== Pflichtfelder (kein Default) =====
    id: int
    timestamp: datetime
    user_id: int
    username: str
    feature: str
    action: str
    log_level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    severity: str   # INFO, WARNING, CRITICAL

    # ===== Optionale Felder (mit Default) =====
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    module: Optional[str] = None
    function: Optional[str] = None
    details: Optional[Dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Konvertiert DTO zu Dictionary (für JSON-Export).

        Returns:
            Dictionary mit allen Feldern
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "username": self.username,
            "feature": self.feature,
            "action": self.action,
            "log_level": self.log_level,
            "severity": self.severity,
            "module": self.module,
            "function": self.function,
            "details": self.details,
            "ip_address": self.ip_address,
            "session_id": self.session_id
        }

    def is_critical(self) -> bool:
        """Prüft, ob Log CRITICAL Severity hat."""
        return self.severity == "CRITICAL"


@dataclass
class CreateAuditLogDTO:
    """
    DTO zum Erstellen eines Audit-Logs.

    Mutable (kein frozen) → Kann vor Validierung bearbeitet werden.
    """
    # ===== Pflichtfelder =====
    user_id: int
    feature: str
    action: str

    # ===== Optionale Felder (mit Defaults) =====
    username: Optional[str] = None
    log_level: str = "INFO"
    severity: str = "INFO"
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    module: Optional[str] = None
    function: Optional[str] = None
    details: Optional[Dict] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validiert Pflichtfelder.

        Raises:
            ValueError: Bei ungültigen Werten
        """
        errors = []

        # user_id >= 0 erlauben (0 = System)
        if self.user_id is None or self.user_id < 0:
            errors.append("user_id must be >= 0 (0 = System)")

        if not self.feature or not self.feature.strip():
            errors.append("feature must not be empty")

        if not self.action or not self.action.strip():
            errors.append("action must not be empty")

        if errors:
            raise ValueError("; ".join(errors))

    def to_audit_log_dto(self, log_id: int) -> AuditLogDTO:
        """
        Konvertiert CreateAuditLogDTO zu AuditLogDTO (nach DB-Insert).

        Args:
            log_id: ID des erstellten Logs

        Returns:
            AuditLogDTO-Instanz
        """
        return AuditLogDTO(
            id=log_id,
            timestamp=datetime.now(),
            user_id=self.user_id,
            username=self.username or f"user_{self.user_id}",
            feature=self.feature,
            action=self.action,
            log_level=self.log_level,
            severity=self.severity,
            module=self.module,
            function=self.function,
            details=self.details or {},
            ip_address=self.ip_address,
            session_id=self.session_id
        )


@dataclass
class AuditLogFilterDTO:
    """
    Filter-Kriterien für Log-Abfragen.

    Alle Felder optional → Flexibles Filtern.
    Kombinierbar mit AND-Logik.
    """
    user_id: Optional[int] = None
    feature: Optional[str] = None
    action: Optional[str] = None
    log_level: Optional[str] = None
    severity: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0

    def to_sql_conditions(self) -> tuple[str, list]:
        """
        Konvertiert Filter zu SQL WHERE-Klausel.

        Returns:
            Tuple (WHERE-String, Parameter-Liste)

        Example:
            >>> filters = AuditLogFilterDTO(user_id=42, feature="auth")
            >>> where, params = filters.to_sql_conditions()
            >>> print(where)  # "user_id = ? AND feature = ?"
            >>> print(params)  # [42, "auth"]
        """
        conditions = []
        params = []

        if self.user_id is not None:
            conditions.append("user_id = ?")
            params.append(self.user_id)

        if self.feature:
            conditions.append("feature = ?")
            params.append(self.feature)

        if self.action:
            conditions.append("action = ?")
            params.append(self.action)

        if self.log_level:
            conditions.append("log_level = ?")
            params.append(self.log_level)

        if self.severity:
            conditions.append("severity = ?")
            params.append(self.severity)

        if self.start_date:
            conditions.append("timestamp >= ?")
            params.append(self.start_date.isoformat())

        if self.end_date:
            conditions.append("timestamp <= ?")
            params.append(self.end_date.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params

    def has_filters(self) -> bool:
        """
        Prüft, ob Filter gesetzt sind.

        Returns:
            True wenn mindestens ein Filter gesetzt
        """
        return any([
            self.user_id is not None,
            self.feature,
            self.action,
            self.log_level,
            self.severity,
            self.start_date,
            self.end_date,
        ])
