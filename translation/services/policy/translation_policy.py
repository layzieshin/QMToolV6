"""
Translation Policy
==================

Authorization policy for translation management operations.

Rules:
------
- VIEW: All authenticated users can read translations
- CREATE/UPDATE:  ADMIN or QMB only
- DELETE: ADMIN only
"""

from typing import Union, Optional

from user_management.dto.user_dto import UserDTO
from user_management.enum.user_enum import SystemRole
from user_management.services.user_management_service_interface import (
    UserManagementServiceInterface,
)
from translation.exceptions.translation_exceptions import TranslationPermissionError


class TranslationPolicy:
    """
    Policy for translation management operations.

    Can operate in two modes:
    1. With UserService (for live user lookups)
    2. With pre-fetched UserDTO (for performance)

    Usage:
    ------
        # Mode 1: With UserService
        >>> policy = TranslationPolicy(user_service)
        >>> policy. can_create_translation(user_id)

        # Mode 2: With UserDTO
        >>> policy = TranslationPolicy()
        >>> policy.can_create_translation(user_dto)
    """

    def __init__(self, user_service: Optional[UserManagementServiceInterface] = None):
        """
        Initialize policy.

        Args:
            user_service: Optional user service for user lookups
        """
        self._user_service = user_service

    def _get_user(self, actor: Union[int, UserDTO]) -> Optional[UserDTO]:
        """
        Internal helper to get UserDTO from int or UserDTO.

        Args:
            actor: User ID (int) or UserDTO

        Returns:
            UserDTO if found/provided

        Raises:
            ValueError: If actor is int but no UserService configured
        """
        if isinstance(actor, UserDTO):
            return actor

        if isinstance(actor, int):
            if not self._user_service:
                raise ValueError(
                    "Cannot resolve user_id without UserService.  "
                    "Either provide UserDTO or initialize policy with UserService."
                )
            return self._user_service.get_user_by_id(actor)

        raise ValueError(f"Actor must be int (user_id) or UserDTO, got {type(actor).__name__}")

    def can_view_translations(self, actor: Union[int, UserDTO]) -> bool:
        """
        Check if actor can view translations (read-only).

        Args:
            actor: User ID or UserDTO

        Returns:
            True if actor is authenticated (any role)

        Example:
        --------
            >>> policy. can_view_translations(user_dto)
            True
        """
        user = self._get_user(actor)
        return user is not None

    def can_create_translation(self, actor: Union[int, UserDTO]) -> bool:
        """
        Check if actor can create translations.

        Args:
            actor: User ID or UserDTO

        Returns:
            True if actor is ADMIN or QMB

        Example:
        --------
            >>> policy.can_create_translation(admin_user)
            True
            >>> policy.can_create_translation(regular_user)
            False
        """
        user = self._get_user(actor)
        if not user:
            return False
        return user.role in (SystemRole.ADMIN, SystemRole.QMB)

    def can_update_translation(self, actor: Union[int, UserDTO]) -> bool:
        """
        Check if actor can update translations.

        Args:
            actor: User ID or UserDTO

        Returns:
            True if actor is ADMIN or QMB
        """
        return self.can_create_translation(actor)

    def can_delete_translation(self, actor: Union[int, UserDTO]) -> bool:
        """
        Check if actor can delete translations.

        Args:
            actor: User ID or UserDTO

        Returns:
            True if actor is ADMIN (only ADMIN can delete)

        Example:
        --------
            >>> policy.can_delete_translation(admin_user)
            True
            >>> policy.can_delete_translation(qmb_user)
            False
        """
        user = self._get_user(actor)
        if not user:
            return False
        return user.role == SystemRole.ADMIN

    def enforce_view(self, actor: Union[int, UserDTO]) -> None:
        """
        Enforce view permission (raise error if denied).

        Raises:
            TranslationPermissionError: If actor cannot view
        """
        if not self.can_view_translations(actor):
            actor_id = actor if isinstance(actor, int) else actor.id
            raise TranslationPermissionError(
                f"Actor {actor_id} lacks permission to view translations (requires authentication)"
            )

    def enforce_create(self, actor: Union[int, UserDTO]) -> None:
        """
        Enforce create permission (raise error if denied).

        Raises:
            TranslationPermissionError: If actor cannot create
        """
        if not self.can_create_translation(actor):
            actor_id = actor if isinstance(actor, int) else actor.id
            raise TranslationPermissionError(
                f"Actor {actor_id} lacks permission to create translations (requires ADMIN/QMB)"
            )

    def enforce_update(self, actor: Union[int, UserDTO]) -> None:
        """
        Enforce update permission (raise error if denied).

        Raises:
            TranslationPermissionError: If actor cannot update
        """
        if not self.can_update_translation(actor):
            actor_id = actor if isinstance(actor, int) else actor.id
            raise TranslationPermissionError(
                f"Actor {actor_id} lacks permission to update translations (requires ADMIN/QMB)"
            )

    def enforce_delete(self, actor: Union[int, UserDTO]) -> None:
        """
        Enforce delete permission (raise error if denied).

        Raises:
            TranslationPermissionError: If actor cannot delete
        """
        if not self.can_delete_translation(actor):
            actor_id = actor if isinstance(actor, int) else actor.id
            raise TranslationPermissionError(
                f"Actor {actor_id} lacks permission to delete translations (requires ADMIN)"
            )