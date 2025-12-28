"""
AuditTrail Exceptions

Definiert alle Exception-Klassen für das AuditTrail-Modul.

Design Principles:
- Hierarchie: Alle erben von AuditException
- Sprechende Namen
- Kontextinformationen in Konstruktor
- Type-Safe Error Handling

Author: QMToolV6 Development Team
Version: 1.0.0
"""


class AuditException(Exception):
    """
    Basis-Exception für alle AuditTrail-Fehler.

    Alle spezifischen Exceptions erben von dieser Klasse.
    Ermöglicht gezieltes Exception-Handling:
    - `except AuditException:` fängt alle AuditTrail-Fehler
    - `except AuditAccessDeniedException:` fängt nur Zugriffsfehler

    Usage:
        >>> try:
        ...     audit.get_logs(filters)
        ... except AuditAccessDeniedException as e:
        ...     print(f"Zugriff verweigert: {e}")
        ... except AuditException as e:
        ...     print(f"Allgemeiner Audit-Fehler: {e}")
    """
    pass


class AuditAccessDeniedException(AuditException):
    """
    User hat keine Berechtigung für die angeforderte Operation.

    Raised when:
    - User versucht fremde Logs zu lesen (kein Admin/QMB)
    - User versucht Logs zu exportieren (kein Admin/QMB)
    - User versucht auf Feature-Logs zuzugreifen (keine Berechtigung)

    Replaces: PermissionError (spezialisiert für AuditTrail)

    Example:
        >>> if not policy.can_read_logs(user_id, filters):
        ...     raise AuditAccessDeniedException(
        ...         f"User {user_id} hat keine Berechtigung zum Lesen der Logs"
        ...     )
    """

    def __init__(self, message: str, user_id: int = None, filters: str = None):
        """
        Args:
            message: Fehlermeldung
            user_id: Optional - ID des betroffenen Users
            filters: Optional - Beschreibung der angeforderten Filter
        """
        super().__init__(message)
        self.user_id = user_id
        self.filters = filters


class FeatureNotFoundException(AuditException):
    """
    Feature existiert nicht oder meta.json nicht gefunden.

    Raised when:
    - Feature-Name ungültig
    - meta.json für Feature nicht vorhanden
    - Feature-Descriptor kann nicht geladen werden

    Replaces: FileNotFoundError (spezialisiert für Features)

    Example:
        >>> try:
        ...     config = configurator.get_feature_meta("invalid_feature")
        ... except Exception as e:
        ...     raise FeatureNotFoundException(f"Feature 'invalid_feature' nicht gefunden: {e}")
    """

    def __init__(self, message: str, feature: str = None):
        """
        Args:
            message: Fehlermeldung
            feature: Optional - Name des gesuchten Features
        """
        super().__init__(message)
        self.feature = feature


class InvalidLogLevelException(AuditException):
    """
    Ungültiger Log-Level oder Severity.

    Raised when:
    - log_level nicht in LogLevel-Enum
    - severity nicht in AuditSeverity-Enum
    - Ungültige Kombination von log_level + severity

    Replaces: ValueError (spezialisiert für Log-Level)

    Example:
        >>> if log_level not in LogLevel:
        ...     raise InvalidLogLevelException(
        ...         f"Ungültiger Log-Level: {log_level}. Erlaubt: {list(LogLevel)}"
        ...     )
    """

    def __init__(self, message: str, level: str = None):
        """
        Args:
            message: Fehlermeldung
            level: Optional - Der ungültige Level-Wert
        """
        super().__init__(message)
        self.level = level


class InvalidAuditLogException(AuditException):
    """
    Log-Eintrag validiert nicht (Pflichtfelder fehlen).

    Raised when:
    - CreateAuditLogDTO.validate() fehlschlägt
    - Pflichtfelder (user_id, feature, action) fehlen
    - Datentypen ungültig

    Replaces: ValueError (spezialisiert für Log-Validierung)

    Example:
        >>> log_dto = CreateAuditLogDTO(user_id=0, feature="", action="TEST")
        >>> try:
        ...     log_dto.validate()
        ... except ValueError as e:
        ...     raise InvalidAuditLogException(f"Invalid log: {e}")
    """

    def __init__(self, message: str, log_dto: dict = None):
        """
        Args:
            message: Fehlermeldung
            log_dto: Optional - Dict-Repräsentation des invaliden Logs
        """
        super().__init__(message)
        self.log_dto = log_dto


class ExportFormatException(AuditException):
    """
    Ungültiges Export-Format.

    Raised when:
    - format nicht in ["json", "csv"]
    - Export-Funktion nicht implementiert

    Example:
        >>> if format not in ["json", "csv"]:
        ...     raise ExportFormatException(
        ...         f"Ungültiges Format: {format}. Erlaubt: json, csv"
        ...     )
    """

    def __init__(self, message: str, format: str = None):
        """
        Args:
            message: Fehlermeldung
            format: Optional - Das ungültige Format
        """
        super().__init__(message)
        self.format = format


class DatabaseException(AuditException):
    """
    Datenbank-Fehler beim Zugriff auf Audit-Logs.

    Raised when:
    - SQLite-Connection fehlschlägt
    - SQL-Query fehlschlägt
    - Tabelle nicht vorhanden

    Example:
        >>> try:
        ...     conn = sqlite3.connect(db_path)
        ... except sqlite3.Error as e:
        ...     raise DatabaseException(f"DB-Fehler: {e}")
    """

    def __init__(self, message: str, original_exception: Exception = None):
        """
        Args:
            message: Fehlermeldung
            original_exception: Optional - Original SQLite-Exception
        """
        super().__init__(message)
        self.original_exception = original_exception
