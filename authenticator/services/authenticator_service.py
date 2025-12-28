"""Authenticator Service Implementation."""
from typing import Optional
import bcrypt

from sqlalchemy.orm import Session

from ..dto.auth_dto import LoginRequestDTO, SessionDTO, AuthenticationResultDTO
from ..repository.session_repository import SessionRepository
from .authenticator_service_interface import AuthenticatorServiceInterface
from .policy.authenticator_policy import AuthenticatorPolicy
from ..exceptions import (
    InvalidCredentialsException,
    PasswordHashingException,
    SessionNotFoundException
)


class AuthenticatorService(AuthenticatorServiceInterface):
    """Service für Authentifizierung."""

    def __init__(
        self,
        db_session: Session,
        user_repository  # Typ aus user_management Modul
    ):
        """
        Initialisiert den Service.

        Args:
            db_session: SQLAlchemy Session
            user_repository: Repository für User-Daten
        """
        self._session_repository = SessionRepository(db_session)
        self._user_repository = user_repository
        self._policy = AuthenticatorPolicy()

    def login(
        self,
        login_request: LoginRequestDTO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuthenticationResultDTO:
        """
        Authentifiziert einen Benutzer.

        Args:
            login_request: Login-Daten
            ip_address: IP-Adresse des Clients
            user_agent: User-Agent des Clients

        Returns:
            AuthenticationResultDTO mit Session-Informationen
        """
        try:
            # Policy-Validierung
            self._policy.validate_login_credentials(
                login_request.username,
                login_request.password
            )

            # Benutzer laden
            user = self._user_repository.get_by_username(login_request.username)

            # Passwort prüfen
            if not self._verify_password(login_request.password, user.password_hash):
                raise InvalidCredentialsException("Ungültige Anmeldedaten")

            # Session erstellen
            session = self._session_repository.create_session(
                user_id=user.id,
                username=user.username,
                ip_address=ip_address,
                user_agent=user_agent
            )

            return AuthenticationResultDTO(
                success=True,
                session=session
            )

        except Exception as e:
            return AuthenticationResultDTO(
                success=False,
                error_message=str(e)
            )

    def logout(self, session_id: str) -> None:
        """
        Beendet eine Session.

        Args:
            session_id: Session-ID
        """
        self._session_repository.delete_session(session_id)

    def validate_session(self, session_id: str) -> SessionDTO:
        """
        Validiert eine Session.

        Args:
            session_id: Session-ID

        Returns:
            SessionDTO wenn Session gültig ist

        Raises:
            SessionNotFoundException: Wenn Session nicht gefunden wurde
            SessionExpiredException: Wenn Session abgelaufen ist
        """
        session = self._session_repository.get_session(session_id)
        self._policy.validate_session(session)
        return session

    def get_session(self, session_id: str) -> SessionDTO:
        """
        Lädt Session-Informationen.

        Args:
            session_id: Session-ID

        Returns:
            SessionDTO
        """
        return self._session_repository.get_session(session_id)

    @staticmethod
    def _verify_password(plain_password: str, password_hash: str) -> bool:
        """
        Verifiziert ein Passwort gegen den Hash.

        Args:
            plain_password: Klartext-Passwort
            password_hash: Gespeicherter Hash

        Returns:
            True wenn Passwort korrekt ist

        Raises:
            PasswordHashingException: Bei Hashing-Fehler
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            raise PasswordHashingException(f"Fehler bei Passwort-Verifikation: {e}")
