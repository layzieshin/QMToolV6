"""
Unit-Tests für UserManagementPolicy.

Testet alle Berechtigungs-Checks für verschiedene Rollen.
"""

import pytest
from ..repository.user_repository import UserRepository
from ..services.policy.user_management_policy import UserManagementPolicy
from ..enum.user_enum import SystemRole


class TestUserManagementPolicy:
    """Test-Suite für UserManagementPolicy."""

    @pytest.fixture
    def setup(self):
        """Erstellt Repository mit Test-Usern."""
        repo = UserRepository()
        policy = UserManagementPolicy(repo)

        admin = repo.create("admin", "hash1", SystemRole.ADMIN)
        user = repo.create("user", "hash2", SystemRole.USER)
        qmb = repo.create("qmb", "hash3", SystemRole.QMB)

        return {
            "repo": repo,
            "policy": policy,
            "admin_id": admin.id,
            "user_id": user.id,
            "qmb_id": qmb.id
        }

    # ===== CREATE USER Tests =====

    def test_admin_can_create_user(self, setup):
        """Test: ADMIN kann User erstellen."""
        assert setup["policy"].can_create_user(setup["admin_id"]) is True

    def test_user_cannot_create_user(self, setup):
        """Test: USER kann keine User erstellen."""
        assert setup["policy"].can_create_user(setup["user_id"]) is False

    def test_qmb_cannot_create_user(self, setup):
        """Test: QMB kann keine User erstellen."""
        assert setup["policy"].can_create_user(setup["qmb_id"]) is False

    def test_non_existing_user_cannot_create(self, setup):
        """Test: Nicht existierender User kann nichts erstellen."""
        assert setup["policy"].can_create_user(999) is False

    # ===== VIEW USER Tests =====

    def test_admin_can_view_any_user(self, setup):
        """Test: ADMIN kann jeden User sehen."""
        assert setup["policy"].can_view_user(setup["admin_id"], setup["user_id"]) is True
        assert setup["policy"].can_view_user(setup["admin_id"], setup["qmb_id"]) is True

    def test_user_can_view_self(self, setup):
        """Test: USER kann sich selbst sehen."""
        assert setup["policy"].can_view_user(setup["user_id"], setup["user_id"]) is True

    def test_user_cannot_view_others(self, setup):
        """Test: USER kann andere nicht sehen."""
        assert setup["policy"].can_view_user(setup["user_id"], setup["admin_id"]) is False

    def test_qmb_can_view_self_only(self, setup):
        """Test: QMB kann nur sich selbst sehen."""
        assert setup["policy"].can_view_user(setup["qmb_id"], setup["qmb_id"]) is True
        assert setup["policy"].can_view_user(setup["qmb_id"], setup["user_id"]) is False

    # ===== VIEW ALL USERS Tests =====

    def test_admin_can_view_all_users(self, setup):
        """Test: ADMIN kann alle User sehen."""
        assert setup["policy"].can_view_all_users(setup["admin_id"]) is True

    def test_user_cannot_view_all_users(self, setup):
        """Test: USER kann nicht alle User sehen."""
        assert setup["policy"].can_view_all_users(setup["user_id"]) is False

    # ===== UPDATE PROFILE Tests =====

    def test_admin_can_update_any_profile(self, setup):
        """Test: ADMIN kann jedes Profil ändern."""
        assert setup["policy"].can_update_profile(setup["admin_id"], setup["user_id"]) is True

    def test_user_can_update_own_profile(self, setup):
        """Test: USER kann eigenes Profil ändern."""
        assert setup["policy"].can_update_profile(setup["user_id"], setup["user_id"]) is True

    def test_user_cannot_update_other_profile(self, setup):
        """Test: USER kann fremdes Profil nicht ändern."""
        assert setup["policy"].can_update_profile(setup["user_id"], setup["admin_id"]) is False

    # ===== CHANGE ROLE Tests =====

    def test_admin_can_change_role(self, setup):
        """Test: ADMIN kann Rollen ändern."""
        assert setup["policy"].can_change_role(setup["admin_id"]) is True

    def test_user_cannot_change_role(self, setup):
        """Test: USER kann Rollen nicht ändern."""
        assert setup["policy"].can_change_role(setup["user_id"]) is False

    # ===== CHANGE PASSWORD Tests =====

    def test_user_can_change_own_password(self, setup):
        """Test: User kann eigenes Passwort ändern."""
        assert setup["policy"].can_change_password(setup["user_id"], setup["user_id"]) is True

    def test_user_cannot_change_other_password(self, setup):
        """Test: User kann fremdes Passwort nicht ändern."""
        assert setup["policy"].can_change_password(setup["user_id"], setup["admin_id"]) is False

    # ===== CHANGE STATUS Tests =====

    def test_admin_can_change_status(self, setup):
        """Test: ADMIN kann Status ändern."""
        assert setup["policy"].can_change_user_status(setup["admin_id"]) is True

    def test_user_cannot_change_status(self, setup):
        """Test: USER kann Status nicht ändern."""
        assert setup["policy"].can_change_user_status(setup["user_id"]) is False
