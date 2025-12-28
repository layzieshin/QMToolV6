"""
Translation Policy Tests
========================

Tests for translation authorization policy.
"""

import pytest

from translation.services.policy.translation_policy import TranslationPolicy
from translation.exceptions.translation_exceptions import TranslationPermissionError
from user_management.enum.user_enum import SystemRole


class TestTranslationPolicy:
    """Tests for TranslationPolicy."""

    def test_can_view_translations_authenticated_user(self, translation_policy, regular_user):
        """Test that any authenticated user can view translations."""
        assert translation_policy.can_view_translations(regular_user) is True
        assert translation_policy.can_view_translations(regular_user.id) is True

    def test_can_view_translations_unauthenticated(self, translation_policy):
        """Test that non-existent user cannot view."""
        assert translation_policy.can_view_translations(999) is False

    def test_can_create_translation_admin(self, translation_policy, admin_user):
        """Test that ADMIN can create translations."""
        assert translation_policy.can_create_translation(admin_user) is True
        assert translation_policy.can_create_translation(admin_user.id) is True

    def test_can_create_translation_qmb(self, translation_policy, qmb_user):
        """Test that QMB can create translations."""
        assert translation_policy.can_create_translation(qmb_user) is True
        assert translation_policy.can_create_translation(qmb_user.id) is True

    def test_can_create_translation_regular_user_denied(self, translation_policy, regular_user):
        """Test that regular USER cannot create translations."""
        assert translation_policy.can_create_translation(regular_user) is False
        assert translation_policy.can_create_translation(regular_user.id) is False

    def test_can_update_translation_admin(self, translation_policy, admin_user):
        """Test that ADMIN can update translations."""
        assert translation_policy.can_update_translation(admin_user) is True

    def test_can_update_translation_qmb(self, translation_policy, qmb_user):
        """Test that QMB can update translations."""
        assert translation_policy.can_update_translation(qmb_user) is True

    def test_can_update_translation_regular_user_denied(self, translation_policy, regular_user):
        """Test that regular USER cannot update translations."""
        assert translation_policy.can_update_translation(regular_user) is False

    def test_can_delete_translation_admin(self, translation_policy, admin_user):
        """Test that ADMIN can delete translations."""
        assert translation_policy.can_delete_translation(admin_user) is True
        assert translation_policy.can_delete_translation(admin_user.id) is True

    def test_can_delete_translation_qmb_denied(self, translation_policy, qmb_user):
        """Test that QMB CANNOT delete translations (ADMIN only)."""
        assert translation_policy.can_delete_translation(qmb_user) is False
        assert translation_policy.can_delete_translation(qmb_user.id) is False

    def test_can_delete_translation_regular_user_denied(self, translation_policy, regular_user):
        """Test that regular USER cannot delete translations."""
        assert translation_policy.can_delete_translation(regular_user) is False

    def test_enforce_create_success(self, translation_policy, admin_user):
        """Test enforce_create does not raise for authorized user."""
        translation_policy.enforce_create(admin_user)  # Should not raise

    def test_enforce_create_raises_error(self, translation_policy, regular_user):
        """Test enforce_create raises error for unauthorized user."""
        with pytest.raises(TranslationPermissionError, match="lacks permission to create"):
            translation_policy.enforce_create(regular_user)

    def test_enforce_update_success(self, translation_policy, qmb_user):
        """Test enforce_update does not raise for authorized user."""
        translation_policy.enforce_update(qmb_user)  # Should not raise

    def test_enforce_update_raises_error(self, translation_policy, regular_user):
        """Test enforce_update raises error for unauthorized user."""
        with pytest.raises(TranslationPermissionError, match="lacks permission to update"):
            translation_policy.enforce_update(regular_user)

    def test_enforce_delete_success(self, translation_policy, admin_user):
        """Test enforce_delete does not raise for ADMIN."""
        translation_policy.enforce_delete(admin_user)  # Should not raise

    def test_enforce_delete_raises_error_for_qmb(self, translation_policy, qmb_user):
        """Test enforce_delete raises error for QMB (ADMIN only)."""
        with pytest.raises(TranslationPermissionError, match="lacks permission to delete"):
            translation_policy.enforce_delete(qmb_user)

    def test_policy_without_user_service_with_dto(self):
        """Test policy can work without UserService if UserDTO provided."""
        from user_management.dto.user_dto import UserDTO
        from user_management.enum.user_enum import UserStatus

        policy = TranslationPolicy(user_service=None)

        admin = UserDTO(
            id=1,
            username="admin",
            full_name="Admin",
            email="admin@test.com",
            role=SystemRole.ADMIN,
            status=UserStatus.ACTIVE
        )

        assert policy.can_create_translation(admin) is True

    def test_policy_without_user_service_with_id_raises_error(self):
        """Test policy raises error if user_id provided without UserService."""
        policy = TranslationPolicy(user_service=None)

        with pytest.raises(ValueError, match="Cannot resolve user_id without UserService"):
            policy.can_create_translation(1)