"""
Unit-Tests für UserRepository.

Testet alle CRUD-Operationen des In-Memory Repositories.
"""

import pytest
from datetime import datetime
from ..repository.user_repository import UserRepository, UserEntity
from ..enum.user_enum import SystemRole, UserStatus


class TestUserRepository:
    """Test-Suite für UserRepository."""

    @pytest.fixture
    def repository(self):
        """Erstellt neues Repository für jeden Test."""
        return UserRepository()

    # ===== CREATE Tests =====

    def test_create_user_success(self, repository):
        """Test: User wird erfolgreich erstellt."""
        user = repository.create("testuser", "hash123", SystemRole.USER, "test@example.com")

        assert user.id == 1
        assert user.username == "testuser"
        assert user.password_hash == "hash123"
        assert user.role == SystemRole.USER
        assert user.email == "test@example.com"
        assert user.status == UserStatus.ACTIVE
        assert isinstance(user.created_at, datetime)
        assert user.last_login_at is None

    def test_create_user_without_email(self, repository):
        """Test: User ohne Email wird erstellt."""
        user = repository.create("nomail", "hash456", SystemRole.ADMIN)

        assert user.email is None

    def test_create_multiple_users_increment_id(self, repository):
        """Test: IDs werden korrekt inkrementiert."""
        user1 = repository.create("user1", "hash1", SystemRole.USER)
        user2 = repository.create("user2", "hash2", SystemRole.QMB)

        assert user1.id == 1
        assert user2.id == 2

    # ===== READ Tests =====

    def test_get_by_id_existing_user(self, repository):
        """Test: User nach ID abrufen."""
        created = repository.create("test", "hash", SystemRole.USER)
        retrieved = repository.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.username == "test"

    def test_get_by_id_non_existing_user(self, repository):
        """Test: Nicht existierender User gibt None zurück."""
        result = repository.get_by_id(999)
        assert result is None

    def test_get_by_username_existing_user(self, repository):
        """Test: User nach Username abrufen."""
        repository.create("findme", "hash", SystemRole.USER)
        retrieved = repository.get_by_username("findme")

        assert retrieved is not None
        assert retrieved.username == "findme"

    def test_get_by_username_non_existing_user(self, repository):
        """Test: Nicht existierender Username gibt None zurück."""
        result = repository.get_by_username("ghost")
        assert result is None

    def test_get_all_users_empty(self, repository):
        """Test: Leeres Repository gibt leere Liste zurück."""
        result = repository.get_all()
        assert result == []

    def test_get_all_users_multiple(self, repository):
        """Test: Alle User werden abgerufen."""
        repository.create("user1", "hash1", SystemRole.USER)
        repository.create("user2", "hash2", SystemRole.ADMIN)
        repository.create("user3", "hash3", SystemRole.QMB)

        result = repository.get_all()
        assert len(result) == 3
        assert {u.username for u in result} == {"user1", "user2", "user3"}

    def test_get_by_role(self, repository):
        """Test: Filter nach Rolle."""
        repository.create("admin1", "hash1", SystemRole.ADMIN)
        repository.create("user1", "hash2", SystemRole.USER)
        repository.create("admin2", "hash3", SystemRole.ADMIN)

        admins = repository.get_by_role(SystemRole.ADMIN)
        assert len(admins) == 2
        assert all(u.role == SystemRole.ADMIN for u in admins)

    def test_get_by_status(self, repository):
        """Test: Filter nach Status."""
        user1 = repository.create("active", "hash1", SystemRole.USER)
        user2 = repository.create("inactive", "hash2", SystemRole.USER)
        user2.status = UserStatus.INACTIVE
        repository.update(user2)

        active_users = repository.get_by_status(UserStatus.ACTIVE)
        assert len(active_users) == 1
        assert active_users[0].username == "active"

    # ===== UPDATE Tests =====

    def test_update_user_success(self, repository):
        """Test: User wird erfolgreich aktualisiert."""
        user = repository.create("update", "hash", SystemRole.USER)
        user.email = "new@example.com"
        user.role = SystemRole.ADMIN

        result = repository.update(user)
        assert result is True

        updated = repository.get_by_id(user.id)
        assert updated.email == "new@example.com"
        assert updated.role == SystemRole.ADMIN

    def test_update_non_existing_user(self, repository):
        """Test: Update eines nicht existierenden Users schlägt fehl."""
        fake_user = UserEntity(999, "fake", "hash", SystemRole.USER)
        result = repository.update(fake_user)
        assert result is False

    # ===== DELETE Tests =====

    def test_delete_existing_user(self, repository):
        """Test: User wird erfolgreich gelöscht."""
        user = repository.create("deleteme", "hash", SystemRole.USER)
        result = repository.delete(user.id)

        assert result is True
        assert repository.get_by_id(user.id) is None

    def test_delete_non_existing_user(self, repository):
        """Test: Löschen eines nicht existierenden Users schlägt fehl."""
        result = repository.delete(999)
        assert result is False
