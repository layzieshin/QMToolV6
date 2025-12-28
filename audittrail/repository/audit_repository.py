"""
AuditTrail Repository

Datenbankzugriff für Audit-Logs.
Implementiert CRUD-Operationen und Query-Funktionen.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Optional

from audittrail.dto.audit_dto import CreateAuditLogDTO, AuditLogDTO, AuditLogFilterDTO


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
            db_path: Pfad zur SQLite\-Datenbankdatei
                     (z\.B. aus Tests: tmp\*.db oder \":memory:\")
        """
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """
        Erstellt Tabellen\-Schema, falls nicht vorhanden.

        Tabelle: audit_logs
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
        """
        self._conn.executescript(schema)
        self._conn.commit()

    def create(self, log_dto: CreateAuditLogDTO) -> int:
        """
        Erstellt neuen Audit\-Log\-Eintrag.

        Args:
            log_dto: CreateAuditLogDTO (ohne id, ohne timestamp)

        Returns:
            id des neu erstellten Logs
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
            log_dto.username,
            log_dto.feature,
            log_dto.action,
            log_dto.log_level,
            log_dto.severity,
            log_dto.ip_address,
            log_dto.session_id,
            log_dto.module,
            log_dto.function,
            json.dumps(log_dto.details) if log_dto.details else None,
        )

        cursor = self._conn.execute(query, params)
        self._conn.commit()
        return cursor.lastrowid

    def find_by_id(self, log_id: int) -> Optional[AuditLogDTO]:
        """
        Findet Log nach ID.

        Args:
            log_id: Log\-ID

        Returns:
            AuditLogDTO oder None
        """
        query = "SELECT * FROM audit_logs WHERE id = ?"
        row = self._conn.execute(query, (log_id,)).fetchone()
        if not row:
            return None
        return self._row_to_dto(row)

    def find_by_filters(self, filters: AuditLogFilterDTO) -> List[AuditLogDTO]:
        """
        Findet Logs nach Filter\-Kriterien.

        Args:
            filters: Filter\-DTO

        Returns:
            Liste von AuditLogDTOs
        """
        where_clause, params = filters.to_sql_conditions()

        query = f"""
            SELECT *
            FROM audit_logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """

        params = list(params)
        params.extend([filters.limit, filters.offset])

        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_dto(r) for r in rows]

    def search_in_details(
        self,
        keyword: str,
        filters: Optional[AuditLogFilterDTO] = None
    ) -> List[AuditLogDTO]:
        """
        Volltext\-Suche in details und action.

        Args:
            keyword: Suchbegriff
            filters: optionale zusätzliche Filter

        Returns:
            Liste von AuditLogDTOs
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

        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_dto(r) for r in rows]

    def search(
        self,
        keyword: str,
        filters: Optional[AuditLogFilterDTO] = None
    ) -> List[AuditLogDTO]:
        """
        Alias für search_in_details(), für API\-Kompatibilität mit Tests.
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
        """
        cutoff_str = cutoff_date.isoformat()

        if feature:
            query = "DELETE FROM audit_logs WHERE timestamp < ? AND feature = ?"
            params = (cutoff_str, feature)
        else:
            query = "DELETE FROM audit_logs WHERE timestamp < ?"
            params = (cutoff_str,)

        cursor = self._conn.execute(query, params)
        self._conn.commit()
        return cursor.rowcount

    def _row_to_dto(self, row: sqlite3.Row) -> AuditLogDTO:
        """
        Konvertiert DB\-Row zu AuditLogDTO.
        """
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
            details=json.loads(row["details"]) if row["details"] else {},
        )

    def close(self) -> None:
        """Schließt Datenbankverbindung."""
        if getattr(self, "_conn", None):
            self._conn.close()
            self._conn = None
