"""Repository for UI events stored in SQLite."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import List

from UI.dto.ui_dto import CreateUIEventDTO, UIEventDTO
from UI.exceptions.ui_exceptions import UIDataLoadError


class UIEventRepository:
    """Stores UI events in a SQLite database."""

    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS ui_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT
        );
        """
        try:
            self._conn.executescript(schema)
            self._conn.commit()
        except sqlite3.Error as exc:
            raise UIDataLoadError(f"Fehler beim Erstellen des UI-Event-Schemas: {exc}") from exc

    def create_event(self, dto: CreateUIEventDTO) -> UIEventDTO:
        """Create a UI event entry."""
        timestamp = datetime.now()
        payload = json.dumps(dto.details) if dto.details else None
        query = """
            INSERT INTO ui_events (timestamp, username, action, details)
            VALUES (?, ?, ?, ?)
        """
        try:
            cursor = self._conn.execute(
                query,
                (timestamp.isoformat(), dto.username, dto.action, payload),
            )
            self._conn.commit()
            return UIEventDTO(
                id=cursor.lastrowid,
                timestamp=timestamp,
                username=dto.username,
                action=dto.action,
                details=dto.details,
            )
        except sqlite3.Error as exc:
            raise UIDataLoadError(f"Fehler beim Schreiben von UI-Events: {exc}") from exc

    def list_events(self, limit: int = 50) -> List[UIEventDTO]:
        """Return the most recent UI events."""
        query = """
            SELECT id, timestamp, username, action, details
            FROM ui_events
            ORDER BY id DESC
            LIMIT ?
        """
        try:
            rows = self._conn.execute(query, (limit,)).fetchall()
        except sqlite3.Error as exc:
            raise UIDataLoadError(f"Fehler beim Lesen von UI-Events: {exc}") from exc

        events: List[UIEventDTO] = []
        for row in rows:
            details = json.loads(row["details"]) if row["details"] else None
            events.append(
                UIEventDTO(
                    id=row["id"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    username=row["username"],
                    action=row["action"],
                    details=details,
                )
            )
        return events
