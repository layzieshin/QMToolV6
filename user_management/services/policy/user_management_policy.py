"""
Policy für UserManagement-Berechtigungen.

Definiert, welche Rollen welche Aktionen ausführen dürfen.
Später erweiterbar für Custom-Rollen.
"""

from ...enum.user_enum import SystemRole
from ...repository.user_repository import UserRepository


class UserManagementPolicy:
    """
    Berechtigungs-Logik für UserManagement.

    Policies sind stateless und verwenden nur übergebene Daten für Checks.
    """

    def __init__(self, repository: UserRepository):
        self._repository = repository

    def can_create_user(self, actor_id: int) -> bool:
        """Nur ADMIN darf User erstellen."""
        actor = self._repository.get_by_id(actor_id)
        return actor is not None and actor.role == SystemRole.ADMIN

    def can_view_user(self, actor_id: int, target_user_id: int) -> bool:
        """
        ADMIN: Kann alle User sehen
        USER/QMB: Kann nur sich selbst sehen
        """
        actor = self._repository.get_by_id(actor_id)
        if actor is None:
            return False
        if actor.role == SystemRole.ADMIN:
            return True
        return actor_id == target_user_id

    def can_view_all_users(self, actor_id: int) -> bool:
        """Nur ADMIN darf alle User sehen."""
        actor = self._repository.get_by_id(actor_id)
        return actor is not None and actor.role == SystemRole.ADMIN

    def can_update_profile(self, actor_id: int, target_user_id: int) -> bool:
        """
        ADMIN: Kann alle Profile ändern
        USER/QMB: Kann nur eigenes Profil ändern
        """
        return self.can_view_user(actor_id, target_user_id)

    def can_change_role(self, actor_id: int) -> bool:
        """Nur ADMIN darf Rollen ändern."""
        actor = self._repository.get_by_id(actor_id)
        return actor is not None and actor.role == SystemRole.ADMIN

    def can_change_password(self, actor_id: int, target_user_id: int) -> bool:
        """User kann nur eigenes Passwort ändern."""
        return actor_id == target_user_id

    def can_change_user_status(self, actor_id: int) -> bool:
        """Nur ADMIN darf User aktivieren/deaktivieren/sperren."""
        actor = self._repository.get_by_id(actor_id)
        return actor is not None and actor.role == SystemRole.ADMIN
