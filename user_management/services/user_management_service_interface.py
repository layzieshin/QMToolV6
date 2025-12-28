"""
Interface für UserManagement Service.

Definiert den Vertrag für Benutzerverwaltung. Entkoppelt die Implementierung
vom Interface und ermöglicht einfaches Testing und zukünftige Erweiterungen.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..dto.user_dto import UserDTO, CreateUserDTO, UpdateUserDTO
from ..enum.user_enum import SystemRole


class UserManagementServiceInterface(ABC):
    """
    Schnittstelle für UserManagement-Operationen.

    Alle Methoden werfen Exceptions bei Fehlern (z.B. UserNotFoundError,
    PermissionDeniedError). Policy-Checks erfolgen vor der Ausführung.
    """

    # ===== CRUD-Operationen =====

    @abstractmethod
    def create_user(self, dto: CreateUserDTO, actor_id: int) -> UserDTO:
        """
        Erstellt einen neuen Benutzer.

        Args:
            dto: Daten für den neuen User
            actor_id: ID des ausführenden Users (für Policy-Check)

        Returns:
            Erstellter User als DTO

        Raises:
            PermissionDeniedError: actor_id hat keine Berechtigung
            UserAlreadyExistsError: Username existiert bereits
        """
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: int, actor_id: int) -> UserDTO:
        """Ruft User nach ID ab."""
        pass

    @abstractmethod
    def get_user_by_username(self, username: str, actor_id: int) -> UserDTO:
        """Ruft User nach Username ab."""
        pass

    @abstractmethod
    def get_all_users(self, actor_id: int) -> List[UserDTO]:
        """Ruft alle User ab."""
        pass

    @abstractmethod
    def get_users_by_role(self, role: SystemRole, actor_id: int) -> List[UserDTO]:
        """Ruft User nach Rolle ab."""
        pass

    @abstractmethod
    def get_active_users(self, actor_id: int) -> List[UserDTO]:
        """Ruft nur aktive User ab."""
        pass

    # ===== Update-Operationen =====

    @abstractmethod
    def update_profile(self, user_id: int, dto: UpdateUserDTO, actor_id: int) -> bool:
        """Aktualisiert User-Profil (Email, etc.)."""
        pass

    @abstractmethod
    def change_role(self, user_id: int, new_role: SystemRole, actor_id: int) -> bool:
        """Ändert die Rolle eines Users (nur ADMIN)."""
        pass

    @abstractmethod
    def change_password(self, user_id: int, old_password: str,
                        new_password: str, actor_id: int) -> bool:
        """Ändert Passwort mit Validierung des alten Passworts."""
        pass

    # ===== Status-Management =====

    @abstractmethod
    def activate_user(self, user_id: int, actor_id: int) -> bool:
        """Aktiviert einen deaktivierten User."""
        pass

    @abstractmethod
    def deactivate_user(self, user_id: int, actor_id: int) -> bool:
        """Deaktiviert einen User (Soft-Delete)."""
        pass

    @abstractmethod
    def lock_user(self, user_id: int, actor_id: int) -> bool:
        """Sperrt einen User (z.B. nach fehlgeschlagenen Logins)."""
        pass

    @abstractmethod
    def unlock_user(self, user_id: int, actor_id: int) -> bool:
        """Entsperrt einen gesperrten User."""
        pass

    # ===== Interne Methoden (für Authenticator) =====

    @abstractmethod
    def update_last_login(self, user_id: int) -> bool:
        """Aktualisiert Zeitstempel des letzten Logins."""
        pass

    @abstractmethod
    def set_password(self, user_id: int, password_hash: str) -> bool:
        """
        Setzt Passwort-Hash direkt (für Authenticator/Reset-Flow).

        Keine Policy-Checks, da diese Methode nur intern vom Authenticator
        aufgerufen wird.
        """
        pass
