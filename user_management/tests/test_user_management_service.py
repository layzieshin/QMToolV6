"""
Integration-Tests für UserManagementService.

Testet die komplette Service-Logik inkl. Policy-Checks und Repository-Interaktion.
"""

import pytest
from ..repository.user_repository import UserRepository
from ..services.user_management_service import UserManagementService
from ..dto.user_dto import CreateUserDTO, UpdateUserDTO
from ..enum.user_enum import SystemRole, UserStatus
from ..exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    PermissionDeniedError,
    InvalidPasswordError
)


class TestUserManagementService:
    """Test-Suite für UserManagementService."""

    @pytest.fixture
    def setup(self):
        """Erstellt Service mit Test-Daten."""
        repo = UserRepository()
        service = UserManagementService(repo)

        # Erstelle Test-Admin (mit direktem Repo-Zugriff, um Policy zu umgehen)
        admin_entity = repo.create("admin", service._hash_password("admin123"), SystemRole.ADMIN)

        return {
            "service": service,
            "admin_id": admin_entity.id
        }

    # ===== CREATE USER Tests =====

    def test_create_user_as_admin_success(self, setup):
        """Test: ADMIN erstellt User erfolgreich."""
        dto = CreateUserDTO(username="newuser", password="pass123", role=SystemRole.USER, email="new@example.com")
        result = setup["service"].create_user(dto, setup["admin_id"])

        assert result.username == "newuser"
        assert result.email == "new@example.com"
        assert result.role == SystemRole.USER
        assert result.status == UserStatus.ACTIVE

    def test_create_user_password_is_hashed(self, setup):
        """Test: Passwort wird gehasht gespeichert."""
        dto = CreateUserDTO(username="hashtest", password="plaintext", role=SystemRole.USER)
        setup["service"].create_user(dto, setup["admin_id"])

        # Passwort sollte nicht im Klartext in Repository sein
        repo = setup["service"]._repository
        user = repo.get_by_username("hashtest")
        assert user.password_hash != "plaintext"
        assert user.password_hash.startswith("$2b$")  # bcrypt prefix

    def test_create_user_duplicate_username(self, setup):
        """Test: Doppelter Username wirft Exception."""
        dto1 = CreateUserDTO(username="duplicate", password="pass1", role=SystemRole.USER)
        setup["service"].create_user(dto1, setup["admin_id"])

        dto2 = CreateUserDTO(username="duplicate", password="pass2", role=SystemRole.ADMIN)
        with pytest.raises(UserAlreadyExistsError):
            setup["service"].create_user(dto2, setup["admin_id"])

    def test_create_user_as_non_admin_fails(self, setup):
        """Test: USER kann keinen User erstellen."""
        # Erstelle normalen User
        user_dto = CreateUserDTO(username="normaluser", password="pass", role=SystemRole.USER)
        user = setup["service"].create_user(user_dto, setup["admin_id"])

        # Versuche als dieser User einen neuen User zu erstellen
        new_dto = CreateUserDTO(username="forbidden", password="pass", role=SystemRole.USER)
        with pytest.raises(PermissionDeniedError):
            setup["service"].create_user(new_dto, user.id)

    # ===== GET USER Tests =====

    def test_get_user_by_id_as_admin(self, setup):
        """Test: ADMIN kann User nach ID abrufen."""
        dto = CreateUserDTO(username="gettest", password="pass", role=SystemRole.USER)
        created = setup["service"].create_user(dto, setup["admin_id"])

        retrieved = setup["service"].get_user_by_id(created.id, setup["admin_id"])
        assert retrieved.id == created.id
        assert retrieved.username == "gettest"

    def test_get_user_by_id_as_self(self, setup):
        """Test: User kann sich selbst abrufen."""
        dto = CreateUserDTO(username="self", password="pass", role=SystemRole.USER)
        user = setup["service"].create_user(dto, setup["admin_id"])

        retrieved = setup["service"].get_user_by_id(user.id, user.id)
        assert retrieved.id == user.id

    def test_get_user_by_id_permission_denied(self, setup):
        """Test: USER kann fremden User nicht abrufen."""
        dto1 = CreateUserDTO(username="user1", password="pass", role=SystemRole.USER)
        dto2 = CreateUserDTO(username="user2", password="pass", role=SystemRole.USER)
        user1 = setup["service"].create_user(dto1, setup["admin_id"])
        user2 = setup["service"].create_user(dto2, setup["admin_id"])

        with pytest.raises(PermissionDeniedError):
            setup["service"].get_user_by_id(user2.id, user1.id)

    def test_get_user_by_id_not_found(self, setup):
        """Test: Nicht existierender User wirft Exception."""
        with pytest.raises(UserNotFoundError):
            setup["service"].get_user_by_id(999, setup["admin_id"])

    def test_get_user_by_username(self, setup):
        """Test: User nach Username abrufen."""
        dto = CreateUserDTO(username="findme", password="pass", role=SystemRole.USER)
        setup["service"].create_user(dto, setup["admin_id"])

        retrieved = setup["service"].get_user_by_username("findme", setup["admin_id"])
        assert retrieved.username == "findme"

    def test_get_all_users_as_admin(self, setup):
        """Test: ADMIN kann alle User sehen."""
        dto1 = CreateUserDTO(username="user1", password="pass", role=SystemRole.USER)
        dto2 = CreateUserDTO(username="user2", password="pass", role=SystemRole.QMB)
        setup["service"].create_user(dto1, setup["admin_id"])
        setup["service"].create_user(dto2, setup["admin_id"])

        users = setup["service"].get_all_users(setup["admin_id"])
        assert len(users) >= 3  # admin + 2 neue

    def test_get_all_users_permission_denied(self, setup):
        """Test: USER kann nicht alle User sehen."""
        dto = CreateUserDTO(username="user", password="pass", role=SystemRole.USER)
        user = setup["service"].create_user(dto, setup["admin_id"])

        with pytest.raises(PermissionDeniedError):
            setup["service"].get_all_users(user.id)

    def test_get_users_by_role(self, setup):
        """Test: Filter nach Rolle."""
        dto1 = CreateUserDTO(username="qmb1", password="pass", role=SystemRole.QMB)
        dto2 = CreateUserDTO(username="qmb2", password="pass", role=SystemRole.QMB)
        setup["service"].create_user(dto1, setup["admin_id"])
        setup["service"].create_user(dto2, setup["admin_id"])

        qmbs = setup["service"].get_users_by_role(SystemRole.QMB, setup["admin_id"])
        assert len(qmbs) == 2
        assert all(u.role == SystemRole.QMB for u in qmbs)

    def test_get_active_users(self, setup):
        """Test: Nur aktive User abrufen."""
        dto = CreateUserDTO(username="active", password="pass", role=SystemRole.USER)
        user = setup["service"].create_user(dto, setup["admin_id"])

        # Deaktiviere User
        setup["service"].deactivate_user(user.id, setup["admin_id"])

        active = setup["service"].get_active_users(setup["admin_id"])
        assert user.id not in [u.id for u in active]

    # ===== UPDATE PROFILE Tests =====

    def test_update_profile_as_self(self, setup):
        """Test: User kann eigenes Profil ändern."""
        dto = CreateUserDTO(username="updateme", password="pass", role=SystemRole.USER, email="old@example.com")
        user = setup["service"].create_user(dto, setup["admin_id"])

        update_dto = UpdateUserDTO(email="new@example.com")
        result = setup["service"].update_profile(user.id, update_dto, user.id)
        assert result is True

        updated = setup["service"].get_user_by_id(user.id, setup["admin_id"])
        assert updated.email == "new@example.com"

    def test_update_profile_permission_denied(self, setup):
        """Test: USER kann fremdes Profil nicht ändern."""
        dto1 = CreateUserDTO(username="user1", password="pass", role=SystemRole.USER)
        dto2 = CreateUserDTO(username="user2", password="pass", role=SystemRole.USER)
        user1 = setup["service"].create_user(dto1, setup["admin_id"])
        user2 = setup["service"].create_user(dto2, setup["admin_id"])

        update_dto = UpdateUserDTO(email="hacked@example.com")
        with pytest.raises(PermissionDeniedError):
            setup["service"].update_profile(user2.id, update_dto, user1.id)

    # ===== CHANGE ROLE Tests =====

    def test_change_role_as_admin(self, setup):
        """Test: ADMIN kann Rolle ändern."""
        dto = CreateUserDTO(username="promote", password="pass", role=SystemRole.USER)
        user = setup["service"].create_user(dto, setup["admin_id"])

        result = setup["service"].change_role(user.id, SystemRole.QMB, setup["admin_id"])
        assert result is True

        updated = setup["service"].get_user_by_id(user.id, setup["admin_id"])
        assert updated.role == SystemRole.QMB

    def test_change_role_permission_denied(self, setup):
        """Test: USER kann Rolle nicht ändern."""
        dto1 = CreateUserDTO(username="user1", password="pass", role=SystemRole.USER)
        dto2 = CreateUserDTO(username="user2", password="pass", role=SystemRole.USER)
        user1 = setup["service"].create_user(dto1, setup["admin_id"])
        user2 = setup["service"].create_user(dto2, setup["admin_id"])

        with pytest.raises(PermissionDeniedError):
            setup["service"].change_role(user2.id, SystemRole.ADMIN, user1.id)

    # ===== CHANGE PASSWORD Tests =====

    def test_change_password_success(self, setup):
        """Test: Passwort-Änderung erfolgreich."""
        dto = CreateUserDTO(username="pwchange", password="oldpass", role=SystemRole.USER)
        user = setup["service"].create_user(dto, setup["admin_id"])

        result = setup["service"].change_password(user.id, "oldpass", "newpass", user.id)
        assert result is True

        # Verifiziere neues Passwort
        repo = setup["service"]._repository
        entity = repo.get_by_id(user.id)
        assert setup["service"]._verify_password("newpass", entity.password_hash) is True

    def test_change_password_wrong_old_password(self, setup):
        """Test: Falsch altes Passwort wirft Exception."""
        dto = CreateUserDTO(username="pwfail", password="correct", role=SystemRole.USER)
        user = setup["service"].create_user(dto, setup["admin_id"])

        with pytest.raises(InvalidPasswordError):
            setup["service"].change_password(user.id, "wrong", "newpass", user.id)

    def test_change_password_permission_denied(self, setup):
        """Test: User kann fremdes Passwort nicht ändern."""
        dto1 = CreateUserDTO(username="user1", password="pass1", role=SystemRole.USER)
        dto2 = CreateUserDTO(username="user2", password="pass2", role=SystemRole.USER)
        user1 = setup["service"].create_user(dto1, setup["admin_id"])
        user2 = setup["service"].create_user(dto2, setup["admin_id"])

        with pytest.raises(PermissionDeniedError):
            setup["service"].change_password(user2.id, "pass2", "hacked", user1.id)

    # ===== STATUS MANAGEMENT Tests =====

    def test_deactivate_user(self, setup):
        """Test: User deaktivieren (Soft-Delete)."""
        dto = CreateUserDTO(username="deactivate", password="pass", role=SystemRole.USER)
        user = setup["service"].create_user(dto, setup["admin_id"])

        result = setup["service"].deactivate_user(user.id, setup["admin_id"])
        assert result is True

        updated = setup["service"].get_user_by_id(user.id, setup["admin_id"])
        assert updated.status == UserStatus.INACTIVE

    def test_activate_user(self, setup):
        """Test: User aktivieren."""
        dto = CreateUserDTO(username="reactivate", password="pass", role=SystemRole.USER)
        user = setup["service"].create_user(dto, setup["admin_id"])
        setup["service"].deactivate_user(user.id, setup["admin_id"])

        result = setup["service"].activate_user(user.id, setup["admin_id"])
        assert result is True

        updated = setup["service"].get_user_by_id(user.id, setup["admin_id"])
        assert updated.status == UserStatus.ACTIVE

    def test_lock_user(self, setup):
        """Test: User sperren."""
        dto = CreateUserDTO(username="lock", password="pass", role=SystemRole.USER)
        user = setup["service"].create_user(dto, setup["admin_id"])

        result = setup["service"].lock_user(user.id, setup["admin_id"])
        assert result is True

        updated = setup["service"].get_user_by_id(user.id, setup["admin_id"])
        assert updated.status == UserStatus.LOCKED

    def test_unlock_user(self, setup):
        """Test: User entsperren."""
        dto = CreateUserDTO(username="unlock", password="pass", role=SystemRole.USER)
        user = setup["service"].create_user(dto, setup["admin_id"])
        setup["service"].lock_user(user.id, setup["admin_id"])

        result = setup["service"].unlock_user(user.id, setup["admin_id"])
        assert result is True

        updated = setup["service"].get_user_by_id(user.id, setup["admin_id"])
        assert updated.status == UserStatus.ACTIVE

    def test_status_change_permission_denied(self, setup):
        """Test: USER kann Status nicht ändern."""
        dto1 = CreateUserDTO(username="user1", password="pass", role=SystemRole.USER)
        dto2 = CreateUserDTO(username="user2", password="pass", role=SystemRole.USER)
        user1 = setup["service"].create_user(dto1, setup["admin_id"])
        user2 = setup["service"].create_user(dto2, setup["admin_id"])

        with pytest.raises(PermissionDeniedError):
            setup["service"].deactivate_user(user2.id, user1.id)

    # ===== INTERNAL METHODS Tests =====

    def test_update_last_login(self, setup):
        """Test: Last-Login Zeitstempel wird aktualisiert."""
        dto = CreateUserDTO(username="logintest", password="pass", role=SystemRole.USER)
        user = setup["service"].create_user(dto, setup["admin_id"])

        result = setup["service"].update_last_login(user.id)
        assert result is True

        updated = setup["service"].get_user_by_id(user.id, setup["admin_id"])
        assert updated.last_login_at is not None

    def test_set_password(self, setup):
        """Test: Passwort-Hash direkt setzen (für Authenticator)."""
        dto = CreateUserDTO(username="setpw", password="pass", role=SystemRole.USER)
        user = setup["service"].create_user(dto, setup["admin_id"])

        new_hash = setup["service"]._hash_password("newpassword")
        result = setup["service"].set_password(user.id, new_hash)
        assert result is True

        repo = setup["service"]._repository
        entity = repo.get_by_id(user.id)
        assert entity.password_hash == new_hash
