"""Repository für Session-Verwaltung."""
from datetime import datetime, timedelta
from typing import Optional
import secrets

from sqlalchemy import Column, Integer, String, DateTime, select
from sqlalchemy.orm import Session

from shared.database.base import Base
from ..dto.auth_dto import SessionDTO
from ..enum.auth_enum import SessionStatus
from ..exceptions import SessionNotFoundException


class SessionEntity(Base):
    """SQLAlchemy Entity für Sessions."""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)


class SessionRepository:
    """Repository für Session-Operationen."""

    def __init__(self, db_session: Session):
        """
        Initialisiert das Repository.

        Args:
            db_session: SQLAlchemy Session
        """
        self._db_session = db_session

    def create_session(
        self,
        user_id: int,
        username: str,
        expires_in_hours: int = 24,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SessionDTO:
        """
        Erstellt eine neue Session.

        Args:
            user_id: ID des Benutzers
            username: Benutzername
            expires_in_hours: Gültigkeitsdauer in Stunden
            ip_address: IP-Adresse des Clients
            user_agent: User-Agent des Clients

        Returns:
            SessionDTO mit Session-Informationen
        """
        now = datetime.now()
        session_id = secrets.token_urlsafe(32)

        entity = SessionEntity(
            session_id=session_id,
            user_id=user_id,
            username=username,
            created_at=now,
            expires_at=now + timedelta(hours=expires_in_hours),
            ip_address=ip_address,
            user_agent=user_agent
        )

        self._db_session.add(entity)
        self._db_session.commit()
        self._db_session.refresh(entity)

        return self._entity_to_dto(entity)

    def get_session(self, session_id: str) -> SessionDTO:
        """
        Lädt eine Session anhand der Session-ID.

        Args:
            session_id: Session-ID

        Returns:
            SessionDTO

        Raises:
            SessionNotFoundException: Wenn Session nicht gefunden wurde
        """
        stmt = select(SessionEntity).where(SessionEntity.session_id == session_id)
        entity = self._db_session.execute(stmt).scalar_one_or_none()

        if not entity:
            raise SessionNotFoundException(f"Session mit ID {session_id} nicht gefunden")

        return self._entity_to_dto(entity)

    def delete_session(self, session_id: str) -> None:
        """
        Löscht eine Session (Logout).

        Args:
            session_id: Session-ID

        Raises:
            SessionNotFoundException: Wenn Session nicht gefunden wurde
        """
        stmt = select(SessionEntity).where(SessionEntity.session_id == session_id)
        entity = self._db_session.execute(stmt).scalar_one_or_none()

        if not entity:
            raise SessionNotFoundException(f"Session mit ID {session_id} nicht gefunden")

        self._db_session.delete(entity)
        self._db_session.commit()

    def delete_user_sessions(self, user_id: int) -> int:
        """
        Löscht alle Sessions eines Benutzers.

        Args:
            user_id: ID des Benutzers

        Returns:
            Anzahl gelöschter Sessions
        """
        stmt = select(SessionEntity).where(SessionEntity.user_id == user_id)
        entities = self._db_session.execute(stmt).scalars().all()

        count = len(entities)
        for entity in entities:
            self._db_session.delete(entity)

        self._db_session.commit()
        return count

    def _entity_to_dto(self, entity: SessionEntity) -> SessionDTO:
        """Konvertiert Entity zu DTO."""
        now = datetime.now()
        status = SessionStatus.ACTIVE if entity.expires_at > now else SessionStatus.EXPIRED

        return SessionDTO(
            session_id=entity.session_id,
            user_id=entity.user_id,
            username=entity.username,
            created_at=entity.created_at,
            expires_at=entity.expires_at,
            status=status,
            ip_address=entity.ip_address,
            user_agent=entity.user_agent
        )
