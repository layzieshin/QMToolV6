"""
AuditTrail Enumerations

Definiert alle Enums für das AuditTrail-Modul:
- LogLevel: Klassische Log-Levels für Entwickler
- AuditSeverity: Compliance-Relevanz für Audits
- AuditActionType: Vordefinierte Action-Types (erweiterbar)

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from enum import Enum


class LogLevel(str, Enum):
    """
    Log-Level für strukturiertes Application Logging.

    Orientiert sich an Standard-Logging-Levels (Python logging, syslog).
    Bestimmt, welche Logs gespeichert werden (via min_log_level).

    Usage:
        >>> from audittrail.enum.audit_enum import LogLevel
        >>> audit.log(user_id=1, action="TEST", feature="app", log_level=LogLevel.DEBUG)
    """
    DEBUG = "DEBUG"          # Detaillierte Entwickler-Infos (nur Dev-Umgebung)
    INFO = "INFO"            # Normale Operationen (Standard)
    WARNING = "WARNING"      # Unerwartete Ereignisse, nicht kritisch
    ERROR = "ERROR"          # Fehler, die behandelt wurden
    CRITICAL = "CRITICAL"    # Schwere Fehler, System-Ausfall


class AuditSeverity(str, Enum):
    """
    Audit-Severity für Compliance-Relevanz.

    Unabhängig von LogLevel - dient zur Kategorisierung für regulatorische Nachweise.
    CRITICAL-Logs können später Email-Benachrichtigungen triggern.

    Usage:
        >>> audit.log(
        ...     user_id=1,
        ...     action="SIGN_DOCUMENT",
        ...     feature="documentlifecycle",
        ...     log_level=LogLevel.INFO,      # Für Entwickler
        ...     severity=AuditSeverity.CRITICAL  # Für Compliance
        ... )
    """
    INFO = "INFO"            # Normale Audit-Events
    WARNING = "WARNING"      # Ungewöhnliche Events, überwachen
    CRITICAL = "CRITICAL"    # Kritische Events, sofortige Aufmerksamkeit


class AuditActionType(str, Enum):
    """
    Vordefinierte Action-Types für häufige Operationen.

    Features können diese nutzen oder eigene String-Actions übergeben.
    Erweiterbar: Neue Actions können direkt als str übergeben werden,
    wenn sie nicht in dieser Enum vorhanden sind.

    Design:
    - Gruppiert nach Features (Auth, User, Document, Config)
    - Großbuchstaben mit Underscore (SCREAMING_SNAKE_CASE)
    - Selbsterklärende Namen

    Usage:
        >>> from audittrail.enum.audit_enum import AuditActionType
        >>> audit.log(
        ...     user_id=1,
        ...     action=AuditActionType.LOGIN,
        ...     feature="authenticator"
        ... )
        >>>
        >>> # Custom Action (nicht in Enum):
        >>> audit.log(
        ...     user_id=1,
        ...     action="CUSTOM_WORKFLOW_STEP",
        ...     feature="documentlifecycle"
        ... )
    """

    # ===== Authenticator =====
    LOGIN = "LOGIN"                        # Erfolgreicher Login
    LOGOUT = "LOGOUT"                      # Logout
    LOGIN_FAILED = "LOGIN_FAILED"          # Fehlgeschlagener Login-Versuch
    SESSION_EXPIRED = "SESSION_EXPIRED"    # Session automatisch abgelaufen

    # ===== User Management =====
    CREATE_USER = "CREATE_USER"            # Neuer User erstellt
    UPDATE_USER = "UPDATE_USER"            # User-Daten geändert
    DELETE_USER = "DELETE_USER"            # User gelöscht
    CHANGE_PASSWORD = "CHANGE_PASSWORD"    # Passwort geändert
    CHANGE_ROLE = "CHANGE_ROLE"            # User-Rolle geändert
    ACTIVATE_USER = "ACTIVATE_USER"        # User aktiviert
    DEACTIVATE_USER = "DEACTIVATE_USER"    # User deaktiviert

    # ===== Document Lifecycle =====
    CREATE_DOCUMENT = "CREATE_DOCUMENT"              # Dokument erstellt
    UPDATE_DOCUMENT = "UPDATE_DOCUMENT"              # Dokument geändert
    DELETE_DOCUMENT = "DELETE_DOCUMENT"              # Dokument gelöscht
    CHANGE_DOCUMENT_STATUS = "CHANGE_DOCUMENT_STATUS" # Status geändert (z.B. Draft → Review)
    START_WORKFLOW = "START_WORKFLOW"                # Workflow gestartet
    COMPLETE_WORKFLOW = "COMPLETE_WORKFLOW"          # Workflow abgeschlossen
    CANCEL_WORKFLOW = "CANCEL_WORKFLOW"              # Workflow abgebrochen
    SIGN_DOCUMENT = "SIGN_DOCUMENT"                  # Dokument signiert (CRITICAL)
    APPROVE_DOCUMENT = "APPROVE_DOCUMENT"            # Dokument freigegeben
    REJECT_DOCUMENT = "REJECT_DOCUMENT"              # Dokument abgelehnt
    ARCHIVE_DOCUMENT = "ARCHIVE_DOCUMENT"            # Dokument archiviert (CRITICAL)

    # ===== Configuration =====
    CHANGE_CONFIG = "CHANGE_CONFIG"        # System-Konfiguration geändert
    CHANGE_FEATURE_CONFIG = "CHANGE_FEATURE_CONFIG"  # Feature-spezifische Config

    # ===== Generic / Debugging =====
    DEBUG_INFO = "DEBUG_INFO"              # Debug-Informationen
    APPLICATION_ERROR = "APPLICATION_ERROR" # Anwendungsfehler
    SYSTEM_ERROR = "SYSTEM_ERROR"          # System-Fehler
    DATABASE_ERROR = "DATABASE_ERROR"      # Datenbank-Fehler

    # ===== AuditTrail selbst =====
    EXPORT_LOGS = "EXPORT_LOGS"            # Logs exportiert
    DELETE_LOGS = "DELETE_LOGS"            # Logs gelöscht (Auto-Cleanup)
    CHANGE_LOG_LEVEL = "CHANGE_LOG_LEVEL"  # Min-Log-Level geändert

    @classmethod
    def get_critical_actions(cls) -> list[str]:
        """
        Gibt Liste der standardmäßig CRITICAL-Actions zurück.

        Diese Actions sollten immer mit severity=CRITICAL geloggt werden,
        unabhängig von Feature-Einstellungen.

        Returns:
            Liste von Action-Namen

        Example:
            >>> critical = AuditActionType.get_critical_actions()
            >>> print(critical)
            ['SIGN_DOCUMENT', 'ARCHIVE_DOCUMENT', 'DELETE_USER', ...]
        """
        return [
            cls.SIGN_DOCUMENT.value,
            cls.ARCHIVE_DOCUMENT.value,
            cls.DELETE_USER.value,
            cls.CHANGE_ROLE.value,
            cls.CHANGE_CONFIG.value,
            cls.DELETE_LOGS.value,
        ]

    @classmethod
    def is_critical(cls, action: str) -> bool:
        """
        Prüft, ob eine Action standardmäßig CRITICAL ist.

        Args:
            action: Action-Name (kann Enum-Value oder String sein)

        Returns:
            True wenn CRITICAL, sonst False

        Example:
            >>> AuditActionType.is_critical("SIGN_DOCUMENT")
            True
            >>> AuditActionType.is_critical("LOGIN")
            False
        """
        return action in cls.get_critical_actions()
