"""Policy für Authenticator-Geschäftsregeln."""
from datetime import datetime
import re

from ...dto.auth_dto import SessionDTO
from ...enum.auth_enum import SessionStatus
from ...exceptions import (
    InvalidCredentialsException,
    SessionExpiredException,
    UserNotAuthenticatedException
)


class AuthenticatorPolicy:
    """Policy für Authenticator-Validierungen."""

    MIN_PASSWORD_LENGTH = 8
    PASSWORD_PATTERN = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'
    )

    @staticmethod
    def validate_login_credentials(username: str, password: str) -> None:
        """
        Validiert Login-Daten.

        Args:
            username: Benutzername
            password: Passwort

        Raises:
            InvalidCredentialsException: Bei ungültigen Daten
        """
        if not username or not username.strip():
            raise InvalidCredentialsException("Benutzername darf nicht leer sein")

        if not password:
            raise InvalidCredentialsException("Passwort darf nicht leer sein")

    @staticmethod
    def validate_password_strength(password: str) -> None:
        """
        Validiert Passwortstärke.

        Args:
            password: Zu validierendes Passwort

        Raises:
            InvalidCredentialsException: Bei schwachem Passwort
        """
        if len(password) < AuthenticatorPolicy.MIN_PASSWORD_LENGTH:
            raise InvalidCredentialsException(
                f"Passwort muss mindestens {AuthenticatorPolicy.MIN_PASSWORD_LENGTH} Zeichen lang sein"
            )

        if not AuthenticatorPolicy.PASSWORD_PATTERN.match(password):
            raise InvalidCredentialsException(
                "Passwort muss mindestens einen Großbuchstaben, einen Kleinbuchstaben, "
                "eine Zahl und ein Sonderzeichen enthalten"
            )

    @staticmethod
    def validate_session(session: SessionDTO) -> None:
        """
        Validiert eine Session.

        Args:
            session: Zu validierende Session

        Raises:
            SessionExpiredException: Wenn Session abgelaufen ist
            UserNotAuthenticatedException: Bei ungültiger Session
        """
        if session.status == SessionStatus.EXPIRED:
            raise SessionExpiredException("Session ist abgelaufen")

        if session.status == SessionStatus.INVALID:
            raise UserNotAuthenticatedException("Session ist ungültig")

        # Zeitbasierte Prüfung
        if session.expires_at < datetime.now():
            raise SessionExpiredException("Session ist abgelaufen")
