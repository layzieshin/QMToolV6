"""Test Fixtures für Authenticator Tests."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from shared.database.base import Base
from ..repository.session_repository import SessionEntity
from ..dto.auth_dto import LoginRequestDTO, SessionDTO
from ..enum.auth_enum import SessionStatus


@pytest.fixture
def db_session() -> Session:
    """Erstellt eine In-Memory Test-Datenbank."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_login_request() -> LoginRequestDTO:
    """Erstellt eine Test-Login-Anfrage."""
    return LoginRequestDTO(
        username="testuser",
        password="Test@1234"
    )


@pytest.fixture
def sample_session_dto() -> SessionDTO:
    """Erstellt ein Test-Session-DTO."""
    now = datetime.now()
    return SessionDTO(
        session_id="test-session-123",
        user_id=1,
        username="testuser",
        created_at=now,
        expires_at=now + timedelta(hours=24),
        status=SessionStatus.ACTIVE,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0"
    )
