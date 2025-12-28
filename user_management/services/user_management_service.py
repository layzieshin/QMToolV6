"""
Implementierung des UserManagement Service.

Enthält die komplette Business-Logik für Benutzerverwaltung.
"""

import bcrypt
from datetime import datetime
from typing import List
from .user_management_service_interface import UserManagementServiceInterface
from ..dto.user_dto import UserDTO, CreateUserDTO, UpdateUserDTO
from ..enum.user_enum import SystemRole, UserStatus
from ..repository.user_repository import UserRepository, UserEntity
from .policy.user_management_policy import UserManagementPolicy
from ..exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    PermissionDeniedError,
    InvalidPasswordError
)


class UserManagementService(UserManagementServiceInterface):
    """Implementierung der UserManagement-Logik."""

    def __init__(self, repository: UserRepository):
        self._repository = repository
        self._policy = UserManagementPolicy(repository)

    # ===== Helper Methods =====

    def _entity_to_dto(self, entity: UserEntity) -> UserDTO:
        """Konvertiert Entity zu DTO."""
        return UserDTO(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            role=entity.role,
            status=entity.status,
            created_at=entity.created_at,
            last_login_at=entity.last_login_at
        )

    def _hash_password(self, password: str) -> str:
        """Hasht Passwort mit bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verifiziert Passwort gegen Hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    # ===== CRUD-Operationen =====

    def create_user(self, dto: CreateUserDTO, actor_id: int) -> UserDTO:
        if not self._policy.can_create_user(actor_id):
            raise PermissionDeniedError("create_user")

        if self._repository.get_by_username(dto.username) is not None:
            raise UserAlreadyExistsError(dto.username)

        password_hash = self._hash_password(dto.password)
        entity = self._repository.create(dto.username, password_hash, dto.role, dto.email)
        return self._entity_to_dto(entity)

    def get_user_by_id(self, user_id: int, actor_id: int) -> UserDTO:
        if not self._policy.can_view_user(actor_id, user_id):
            raise PermissionDeniedError("get_user_by_id")

        entity = self._repository.get_by_id(user_id)
        if entity is None:
            raise UserNotFoundError(f"ID: {user_id}")

        return self._entity_to_dto(entity)

    def get_user_by_username(self, username: str, actor_id: int) -> UserDTO:
        entity = self._repository.get_by_username(username)
        if entity is None:
            raise UserNotFoundError(f"Username: {username}")

        if not self._policy.can_view_user(actor_id, entity.id):
            raise PermissionDeniedError("get_user_by_username")

        return self._entity_to_dto(entity)

    def get_all_users(self, actor_id: int) -> List[UserDTO]:
        if not self._policy.can_view_all_users(actor_id):
            raise PermissionDeniedError("get_all_users")

        entities = self._repository.get_all()
        return [self._entity_to_dto(e) for e in entities]

    def get_users_by_role(self, role: SystemRole, actor_id: int) -> List[UserDTO]:
        if not self._policy.can_view_all_users(actor_id):
            raise PermissionDeniedError("get_users_by_role")

        entities = self._repository.get_by_role(role)
        return [self._entity_to_dto(e) for e in entities]

    def get_active_users(self, actor_id: int) -> List[UserDTO]:
        if not self._policy.can_view_all_users(actor_id):
            raise PermissionDeniedError("get_active_users")

        entities = self._repository.get_by_status(UserStatus.ACTIVE)
        return [self._entity_to_dto(e) for e in entities]

    # ===== Update-Operationen =====

    def update_profile(self, user_id: int, dto: UpdateUserDTO, actor_id: int) -> bool:
        if not self._policy.can_update_profile(actor_id, user_id):
            raise PermissionDeniedError("update_profile")

        entity = self._repository.get_by_id(user_id)
        if entity is None:
            raise UserNotFoundError(f"ID: {user_id}")

        if dto.email is not None:
            entity.email = dto.email

        return self._repository.update(entity)

    def change_role(self, user_id: int, new_role: SystemRole, actor_id: int) -> bool:
        if not self._policy.can_change_role(actor_id):
            raise PermissionDeniedError("change_role")

        entity = self._repository.get_by_id(user_id)
        if entity is None:
            raise UserNotFoundError(f"ID: {user_id}")

        entity.role = new_role
        return self._repository.update(entity)

    def change_password(self, user_id: int, old_password: str,
                       new_password: str, actor_id: int) -> bool:
        if not self._policy.can_change_password(actor_id, user_id):
            raise PermissionDeniedError("change_password")

        entity = self._repository.get_by_id(user_id)
        if entity is None:
            raise UserNotFoundError(f"ID: {user_id}")

        if not self._verify_password(old_password, entity.password_hash):
            raise InvalidPasswordError()

        entity.password_hash = self._hash_password(new_password)
        return self._repository.update(entity)

    # ===== Status-Management =====

    def activate_user(self, user_id: int, actor_id: int) -> bool:
        if not self._policy.can_change_user_status(actor_id):
            raise PermissionDeniedError("activate_user")

        entity = self._repository.get_by_id(user_id)
        if entity is None:
            raise UserNotFoundError(f"ID: {user_id}")

        entity.status = UserStatus.ACTIVE
        return self._repository.update(entity)

    def deactivate_user(self, user_id: int, actor_id: int) -> bool:
        if not self._policy.can_change_user_status(actor_id):
            raise PermissionDeniedError("deactivate_user")

        entity = self._repository.get_by_id(user_id)
        if entity is None:
            raise UserNotFoundError(f"ID: {user_id}")

        entity.status = UserStatus.INACTIVE
        return self._repository.update(entity)

    def lock_user(self, user_id: int, actor_id: int) -> bool:
        if not self._policy.can_change_user_status(actor_id):
            raise PermissionDeniedError("lock_user")

        entity = self._repository.get_by_id(user_id)
        if entity is None:
            raise UserNotFoundError(f"ID: {user_id}")

        entity.status = UserStatus.LOCKED
        return self._repository.update(entity)

    def unlock_user(self, user_id: int, actor_id: int) -> bool:
        if not self._policy.can_change_user_status(actor_id):
            raise PermissionDeniedError("unlock_user")

        entity = self._repository.get_by_id(user_id)
        if entity is None:
            raise UserNotFoundError(f"ID: {user_id}")

        entity.status = UserStatus.ACTIVE
        return self._repository.update(entity)

    # ===== Interne Methoden =====

    def update_last_login(self, user_id: int) -> bool:
        entity = self._repository.get_by_id(user_id)
        if entity is None:
            return False

        entity.last_login_at = datetime.now()
        return self._repository.update(entity)

    def set_password(self, user_id: int, password_hash: str) -> bool:
        entity = self._repository.get_by_id(user_id)
        if entity is None:
            return False

        entity.password_hash = password_hash
        return self._repository.update(entity)
