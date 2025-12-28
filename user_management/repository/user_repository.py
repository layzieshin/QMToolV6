"""
Repository für User-Datenzugriff.

Vorerst In-Memory-Implementierung. Später einfach durch DB-Repository ersetzbar
(z.B. SQLAlchemy), da das Interface identisch bleibt.
"""

from datetime import datetime
from typing import List, Optional, Dict
from ..dto.user_dto import UserDTO, CreateUserDTO
from ..enum.user_enum import SystemRole, UserStatus


class UserEntity:
    """Interne Entity (später ORM-Modell)."""
    def __init__(self, id: int, username: str, password_hash: str,
                 role: SystemRole, email: Optional[str] = None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.email = email
        self.status = UserStatus.ACTIVE
        self.created_at = datetime.now()
        self.last_login_at: Optional[datetime] = None


class UserRepository:
    """
    In-Memory Repository für User-Daten.

    Thread-Safety ist hier NICHT implementiert (für Produktiv-Code mit
    Threading `threading.Lock` verwenden oder DB-Transaktionen nutzen).
    """

    def __init__(self):
        self._users: Dict[int, UserEntity] = {}
        self._next_id = 1

    def create(self, username: str, password_hash: str, role: SystemRole,
               email: Optional[str] = None) -> UserEntity:
        """Erstellt neuen User."""
        user = UserEntity(self._next_id, username, password_hash, role, email)
        self._users[self._next_id] = user
        self._next_id += 1
        return user

    def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        """Ruft User nach ID ab."""
        return self._users.get(user_id)

    def get_by_username(self, username: str) -> Optional[UserEntity]:
        """Ruft User nach Username ab."""
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def get_all(self) -> List[UserEntity]:
        """Ruft alle User ab."""
        return list(self._users.values())

    def get_by_role(self, role: SystemRole) -> List[UserEntity]:
        """Ruft User nach Rolle ab."""
        return [u for u in self._users.values() if u.role == role]

    def get_by_status(self, status: UserStatus) -> List[UserEntity]:
        """Ruft User nach Status ab."""
        return [u for u in self._users.values() if u.status == status]

    def update(self, user: UserEntity) -> bool:
        """Aktualisiert User (In-Memory: Referenz wird geändert)."""
        if user.id in self._users:
            self._users[user.id] = user
            return True
        return False

    def delete(self, user_id: int) -> bool:
        """Hard-Delete (für DSGVO-Fälle)."""
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False
