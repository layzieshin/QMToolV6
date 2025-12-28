"""Tests für SessionRepository."""
import pytest
from datetime import datetime, timedelta

from ..repository.session_repository import SessionRepository, SessionEntity
from ..enum.auth_enum import SessionStatus
from ..exceptions import SessionNotFoundException


class TestSessionRepository:
    """Tests für SessionRepository."""

    def test_create_session_success(self, db_session):
        """Test: Session erfolgreich erstellen."""
        # Arrange
        repo = SessionRepository(db_session)
        user_id = 1
        username = "testuser"

        # Act
        session = repo.create_session(
            user_id=user_id,
            username=username,
            ip_address="127.0.0.1",
            user_agent="TestAgent/1.0"
        )

        # Assert
        assert session.user_id == user_id
        assert session.username == username
        assert session.status == SessionStatus.ACTIVE
        assert session.ip_address == "127.0.0.1"
        assert len(session.session_id) > 0

    def test_get_session_success(self, db_session):
        """Test: Session erfolgreich laden."""
        # Arrange
        repo = SessionRepository(db_session)
        created = repo.create_session(user_id=1, username="testuser")

        # Act
        loaded = repo.get_session(created.session_id)

        # Assert
        assert loaded.session_id == created.session_id
        assert loaded.user_id == created.user_id
        assert loaded.username == created.username

    def test_get_session_not_found(self, db_session):
        """Test: Session nicht gefunden."""
        # Arrange
        repo = SessionRepository(db_session)

        # Act & Assert
        with pytest.raises(SessionNotFoundException):
            repo.get_session("nonexistent-session-id")

    def test_delete_session_success(self, db_session):
        """Test: Session erfolgreich löschen."""
        # Arrange
        repo = SessionRepository(db_session)
        session = repo.create_session(user_id=1, username="testuser")

        # Act
        repo.delete_session(session.session_id)

        # Assert
        with pytest.raises(SessionNotFoundException):
            repo.get_session(session.session_id)

    def test_delete_user_sessions(self, db_session):
        """Test: Alle Sessions eines Users löschen."""
        # Arrange
        repo = SessionRepository(db_session)
        user_id = 1
        repo.create_session(user_id=user_id, username="testuser")
        repo.create_session(user_id=user_id, username="testuser")
        repo.create_session(user_id=2, username="otheruser")

        # Act
        deleted_count = repo.delete_user_sessions(user_id)

        # Assert
        assert deleted_count == 2

    def test_session_expiration(self, db_session):
        """Test: Abgelaufene Session wird erkannt."""
        # Arrange
        repo = SessionRepository(db_session)
        now = datetime.now()

        entity = SessionEntity(
            session_id="expired-session",
            user_id=1,
            username="testuser",
            created_at=now - timedelta(hours=25),
            expires_at=now - timedelta(hours=1)
        )
        db_session.add(entity)
        db_session.commit()

        # Act
        session = repo.get_session("expired-session")

        # Assert
        assert session.status == SessionStatus.EXPIRED
