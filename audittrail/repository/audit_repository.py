"""
AuditTrail Repository

Datenbankzugriff für Audit-Logs.
Implementiert CRUD-Operationen und Query-Funktionen.

Author: QMToolV6 Development Team
Version: 1.1.0
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Optional

from audittrail.dto. audit_dto import CreateAuditLogDTO, AuditLogDTO, AuditLogFilterDTO
from audittrail.exceptions. audit_exceptions import DatabaseException


class AuditRepository:
    """
    Repository für Audit-Log-Zugriff.

    Verwendet SQLite als Datenbank-Backend.
    Tabellen-Schema wird automatisch erstellt, falls nicht vorhanden.
    """

    def __init__(self, db_path: str):
        """
        Initialisiert Repository.

        Args:
            db_path: Pfad zur SQLite-Datenbankdatei
                     (z.B. aus Tests:  tmp*. db oder ": memory:")
        """
        try:
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._ensure_schema()
        except sqlite3.Error as e:
            raise DatabaseException(
                f"Fehler beim Verbinden mit Datenbank '{db_path}': {str(e)}",
                original_exception=e
            )

    def _ensure_schema(self) -> None:
        """
        Erstellt Tabellen-Schema, falls nicht vorhanden.

        Tabelle:  audit_logs
        """
        schema = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            feature TEXT NOT NULL,
            action TEXT NOT NULL,
            log_level TEXT NOT NULL,
            severity TEXT NOT NULL,
            ip_address TEXT,
            session_id TEXT,
            module TEXT,
            function TEXT,
            details TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_feature ON audit_logs(feature);
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_logs(severity);
        CREATE INDEX IF NOT EXISTS idx_audit_log_level ON audit_logs(log_level);
        """
        try:
            self._conn.executescript(schema)
            self._conn.commit()
        except sqlite3.Error as e:
            raise DatabaseException(
                f"Fehler beim Erstellen des Schemas: {str(e)}",
                original_exception=e
            )

    def create(self, log_dto: CreateAuditLogDTO) -> int:
        """
        Erstellt neuen Audit-Log-Eintrag.

        Args:
            log_dto: CreateAuditLogDTO (ohne id, ohne timestamp)

        Returns:
            id des neu erstellten Logs

        Raises:
            DatabaseException: Bei DB-Fehlern
        """
        # DTO validieren (wirft ValueError bei Fehler)
        log_dto.validate()

        # Timestamp hier generieren
        timestamp = datetime.now().isoformat()

        query = """
            INSERT INTO audit_logs (
                timestamp, user_id, username, feature, action,
                log_level, severity, ip_address, session_id,
                module, function, details
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            timestamp,
            log_dto.user_id,
            log_dto. username or f"user_{log_dto.user_id}",
            log_dto.feature,
            log_dto.action,
            log_dto.log_level,
            log_dto.severity,
            log_dto.ip_address,
            log_dto.session_id,
            log_dto. module,
            log_dto. function,
            json.dumps(log_dto.details) if log_dto.details else None,
        )

        try:
            cursor = self._conn.execute(query, params)
            self._conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            raise DatabaseException(
                f"Fehler beim Erstellen des Logs: {str(e)}",
                original_exception=e
            )

    def find_by_id(self, log_id: int) -> Optional[AuditLogDTO]:
        """
        Findet Log nach ID.

        Args:
            log_id: Log-ID

        Returns:
            AuditLogDTO oder None

        Raises:
            DatabaseException: Bei DB-Fehlern
        """
        query = "SELECT * FROM audit_logs WHERE id = ?"
        try:
            row = self._conn.execute(query, (log_id,)).fetchone()
            if not row:
                return None
            return self._row_to_dto(row)
        except sqlite3.Error as e:
            raise DatabaseException(
                f"Fehler beim Suchen von Log {log_id}: {str(e)}",
                original_exception=e
            )

    def find_by_filters(self, filters: AuditLogFilterDTO) -> List[AuditLogDTO]:
        """
        Findet Logs nach Filter-Kriterien.

        Args:
            filters: Filter-DTO

        Returns:
            Liste von AuditLogDTOs

        Raises:
            DatabaseException: Bei DB-Fehlern
        """
        where_clause, params = filters.to_sql_conditions()

        query = f"""
            SELECT *
            FROM audit_logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?  OFFSET ?
        """

        params = list(params)
        params.extend([filters.limit, filters.offset])

        try:
            rows = self._conn.execute(query, params).fetchall()
            return [self._row_to_dto(r) for r in rows]
        except sqlite3.Error as e:
            raise DatabaseException(
                f"Fehler beim Filtern von Logs: {str(e)}",
                original_exception=e
            )

    def search_in_details(
        self,
        keyword: str,
        filters: Optional[AuditLogFilterDTO] = None
    ) -> List[AuditLogDTO]:
        """
        Volltext-Suche in details und action.

        Args:
            keyword: Suchbegriff
            filters: optionale zusätzliche Filter

        Returns:
            Liste von AuditLogDTOs

        Raises:
            DatabaseException: Bei DB-Fehlern
        """
        if filters is None:
            filters = AuditLogFilterDTO()

        where_clause, params = filters.to_sql_conditions()

        query = f"""
            SELECT *
            FROM audit_logs
            WHERE {where_clause}
              AND (details LIKE ? OR action LIKE ?)
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ? 
        """

        params = list(params)
        pattern = f"%{keyword}%"
        params.extend([pattern, pattern, filters.limit, filters.offset])

        try:
            rows = self._conn.execute(query, params).fetchall()
            return [self._row_to_dto(r) for r in rows]
        except sqlite3.Error as e:
            raise DatabaseException(
                f"Fehler bei der Suche nach '{keyword}': {str(e)}",
                original_exception=e
            )

    def search(
        self,
        keyword:  str,
        filters: Optional[AuditLogFilterDTO] = None
    ) -> List[AuditLogDTO]:
        """
        Alias für search_in_details(), für API-Kompatibilität mit Tests.
        """
        return self.search_in_details(keyword, filters)

    def delete_before(
        self,
        cutoff_date: datetime,
        feature: Optional[str] = None
    ) -> int:
        """
        Löscht Logs vor cutoff_date, optional eingeschränkt auf Feature.

        Args:
            cutoff_date: Datum, vor dem gelöscht werden soll
            feature: optionales Feature

        Returns:
            Anzahl gelöschter Logs

        Raises:
            DatabaseException: Bei DB-Fehlern
        """
        cutoff_str = cutoff_date.isoformat()

        if feature:
            query = "DELETE FROM audit_logs WHERE timestamp < ?  AND feature = ?"
            params = (cutoff_str, feature)
        else:
            query = "DELETE FROM audit_logs WHERE timestamp < ?"
            params = (cutoff_str,)

        try:
            cursor = self._conn.execute(query, params)
            self._conn.commit()
            return cursor. rowcount
        except sqlite3.Error as e:
            raise DatabaseException(
                f"Fehler beim Löschen alter Logs: {str(e)}",
                original_exception=e
            )

    def _row_to_dto(self, row:  sqlite3.Row) -> AuditLogDTO:
        """
        Konvertiert DB-Row zu AuditLogDTO.
        """
        try:
            details_json = row["details"]
            details = json.loads(details_json) if details_json else {}
        except (json.JSONDecodeError, TypeError):
            details = {}

        return AuditLogDTO(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            user_id=row["user_id"],
            username=row["username"],
            feature=row["feature"],
            action=row["action"],
            log_level=row["log_level"],
            severity=row["severity"],
            ip_address=row["ip_address"],
            session_id=row["session_id"],
            module=row["module"],
            function=row["function"],
            details=details,
        )

    def close(self) -> None:
        """Schließt Datenbankverbindung."""
        if hasattr(self, "_conn") and self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass  # Ignoriere Fehler beim Schließen
            finally:
                del self._conn  # Entferne Referenz statt None-Zuweisung