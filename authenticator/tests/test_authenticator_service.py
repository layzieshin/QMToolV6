"""Tests für AuthenticatorService."""
import pytest
from unittest.mock import Mock, MagicMock
import bcrypt

from ..services.authenticator_service import AuthenticatorService
from ..dto.auth_dto import LoginRequestDTO
from ..exceptions import InvalidCredentialsException


class TestAuthenticatorService:
    """Tests für AuthenticatorService."""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock für User Repository."""
        mock = Mock()
        user = Mock()
        user.id = 1
        user.username = "testuser"
        user.password_hash = bcrypt.hashpw(
            "Test@1234".encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        mock.get_by_username.return_value = user
        return mock

    @pytest.fixture
    def service(self, db_session, mock_user_repository):
        """Erstellt Service-Instanz."""
        return AuthenticatorService(db_session, mock_user_repository)

    def test_login_success(self, service, sample_login_request):
        """Test: Erfolgreicher Login."""
        # Act
        result = service.login(sample_login_request, "127.0.0.1", "TestAgent/1.0")

        # Assert
        assert result.success is True
        assert result.session is not None
        assert result.session.username == "testuser"
        assert result.error_message is None

    def test_login_invalid_password(self, service, sample_login_request):
        """Test: Login mit falschem Passwort."""
        # Arrange
        sample_login_request.password = "WrongPassword@123"

        # Act
        result = service.login(sample_login_request)

        # Assert
        assert result.success is False
        assert result.session is None
        assert result.error_message is not None

    def test_logout_success(self, service, sample_login_request):
        """Test: Erfolgreicher Logout."""
        # Arrange
        login_result = service.login(sample_login_request)

        # Act & Assert (keine Exception)
        service.logout(login_result.session.session_id)

    def test_validate_session_success(self, service, sample_login_request):
        """Test: Session validieren."""
        # Arrange
        login_result = service.login(sample_login_request)

        # Act
        session = service.validate_session(login_result.session.session_id)

        # Assert
        assert session.session_id == login_result.session.session_id

    def test_get_session(self, service, sample_login_request):
        """Test: Session-Informationen laden."""
        # Arrange
        login_result = service.login(sample_login_request)

        # Act
        session = service.get_session(login_result.session.session_id)

        # Assert
        assert session.username == "testuser"
