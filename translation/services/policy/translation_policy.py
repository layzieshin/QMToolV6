from user_management.enum.user_enum import SystemRole
from user_management.services.user_management_service_interface import UserManagementServiceInterface
from translation.exceptions.translation_exceptions import TranslationPermissionError


class TranslationPolicy:
    """
    Policy for translation management operations.

    Rules:
    - VIEW:  All authenticated users can read translations
    - CREATE/UPDATE:  ADMIN or QMB only
    - DELETE: ADMIN only
    """

    def __init__(self, user_service: UserManagementServiceInterface):
        self._user_service = user_service

    def can_view_translations(self, actor_id: int) -> bool:
        """Anyone can view (read-only)."""
        user = self._user_service.get_user_by_id(actor_id)
        return user is not None  # Authenticated users only

    def can_create_translation(self, actor_id: int) -> bool:
        """ADMIN or QMB can create."""
        user = self._user_service.get_user_by_id(actor_id)
        if not user:
            return False
        return user.role in (SystemRole.ADMIN, SystemRole.QMB)

    def can_update_translation(self, actor_id: int) -> bool:
        """ADMIN or QMB can update."""
        return self.can_create_translation(actor_id)

    def can_delete_translation(self, actor_id: int) -> bool:
        """Only ADMIN can delete."""
        user = self._user_service.get_user_by_id(actor_id)
        if not user:
            return False
        return user.role == SystemRole.ADMIN

    def enforce_create(self, actor_id: int) -> None:
        """Raise error if actor cannot create."""
        if not self.can_create_translation(actor_id):
            raise TranslationPermissionError(
                f"Actor {actor_id} lacks permission to create translations (requires ADMIN/QMB)"
            )

    def enforce_update(self, actor_id: int) -> None:
        """Raise error if actor cannot update."""
        if not self.can_update_translation(actor_id):
            raise TranslationPermissionError(
                f"Actor {actor_id} lacks permission to update translations (requires ADMIN/QMB)"
            )

    def enforce_delete(self, actor_id: int) -> None:
        """Raise error if actor cannot delete."""
        if not self.can_delete_translation(actor_id):
            raise TranslationPermissionError(
                f"Actor {actor_id} lacks permission to delete translations (requires ADMIN)"
            )