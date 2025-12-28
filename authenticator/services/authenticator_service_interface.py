"""Interface für Authenticator Service."""
from abc import ABC, abstractmethod
from typing import Optional

from ..dto.auth_dto import LoginRequestDTO, SessionDTO, AuthenticationResultDTO


class AuthenticatorServiceInterface(ABC):
    """Interface für Authenticator-Service."""

    @abstractmethod
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
        pass

    @abstractmethod
    def logout(self, session_id: str) -> None:
        """
        Beendet eine Session.

        Args:
            session_id: Session-ID
        """
        pass

    @abstractmethod
    def validate_session(self, session_id: str) -> SessionDTO:
        """
        Validiert eine Session.

        Args:
            session_id: Session-ID

        Returns:
            SessionDTO wenn Session gültig ist
        """
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> SessionDTO:
        """
        Lädt Session-Informationen.

        Args:
            session_id: Session-ID

        Returns:
            SessionDTO
        """
        pass
