"""Tests für AuthenticatorPolicy."""
import pytest
from datetime import datetime, timedelta

from ..services.policy.authenticator_policy import AuthenticatorPolicy
from ..dto.auth_dto import SessionDTO
from ..enum.auth_enum import SessionStatus
from ..exceptions import (
    InvalidCredentialsException,
    SessionExpiredException,
    UserNotAuthenticatedException
)


class TestAuthenticatorPolicy:
    """Tests für AuthenticatorPolicy."""

    def test_validate_login_credentials_success(self):
        """Test: Gültige Login-Daten."""
        # Act & Assert (keine Exception)
        AuthenticatorPolicy.validate_login_credentials("testuser", "password")

    def test_validate_login_credentials_empty_username(self):
        """Test: Leerer Benutzername."""
        # Act & Assert
        with pytest.raises(InvalidCredentialsException):
            AuthenticatorPolicy.validate_login_credentials("", "password")

    def test_validate_login_credentials_empty_password(self):
        """Test: Leeres Passwort."""
        # Act & Assert
        with pytest.raises(InvalidCredentialsException):
            AuthenticatorPolicy.validate_login_credentials("testuser", "")

    def test_validate_password_strength_success(self):
        """Test: Starkes Passwort."""
        # Act & Assert
        AuthenticatorPolicy.validate_password_strength("Test@1234")

    def test_validate_password_strength_too_short(self):
        """Test: Zu kurzes Passwort."""
        # Act & Assert
        with pytest.raises(InvalidCredentialsException):
            AuthenticatorPolicy.validate_password_strength("Test@1")

    def test_validate_password_strength_no_uppercase(self):
        """Test: Kein Großbuchstabe."""
        # Act & Assert
        with pytest.raises(InvalidCredentialsException):
            AuthenticatorPolicy.validate_password_strength("test@1234")

    def test_validate_session_active(self, sample_session_dto):
        """Test: Aktive Session validieren."""
        # Act & Assert
        AuthenticatorPolicy.validate_session(sample_session_dto)

    def test_validate_session_expired(self, sample_session_dto):
        """Test: Abgelaufene Session."""
        # Arrange
        sample_session_dto.status = SessionStatus.EXPIRED

        # Act & Assert
        with pytest.raises(SessionExpiredException):
            AuthenticatorPolicy.validate_session(sample_session_dto)

    def test_validate_session_invalid(self, sample_session_dto):
        """Test: Ungültige Session."""
        # Arrange
        sample_session_dto.status = SessionStatus.INVALID

        # Act & Assert
        with pytest.raises(UserNotAuthenticatedException):
            AuthenticatorPolicy.validate_session(sample_session_dto)
