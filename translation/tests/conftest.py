"""
Translation Test Fixtures
==========================

Shared pytest fixtures for Translation feature tests.

Key idea:
- Do NOT instantiate UserDTO directly in tests unless you fully control its constructor.
  The UserDTO signature may evolve, which would break fixtures and cascade into dozens of errors.
- Instead, we use a Mock(spec=UserDTO) and explicitly set the attributes the translation policy/service needs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict
from unittest.mock import Mock

import pytest

from translation.repository.translation_repository import InMemoryTranslationRepository
from translation.services.feature_discovery_service import FeatureDiscoveryService
from translation.services.policy.translation_policy import TranslationPolicy
from translation.services.translation_service import TranslationService
from user_management.dto.user_dto import UserDTO
from user_management.enum.user_enum import SystemRole
from user_management.enum.user_enum import UserStatus


@pytest.fixture
def translation_repository() -> InMemoryTranslationRepository:
    """Return a fresh in-memory repository for each test."""
    return InMemoryTranslationRepository()


@pytest.fixture
def sample_translations() -> Dict[str, object]:
    """
    Provide a small but representative translation dataset.

    Note:
    - The structure here must match what create_translation_set expects in your repository implementation.
    - We keep the fixture generic and let tests define their own strict expectations.
    """
    # Keep this as-is if your test-suite depends on it.
    # If you want me to align it precisely with TranslationSetDTO, upload that DTO file and I’ll normalize it.
    return {}


@pytest.fixture
def populated_repository(
    translation_repository: InMemoryTranslationRepository,
    sample_translations: Dict[str, object],
) -> InMemoryTranslationRepository:
    """Return repository populated with sample data (if any fixture data is provided)."""
    for trans_set in sample_translations.values():
        translation_repository.create_translation_set(trans_set)
    return translation_repository


@pytest.fixture
def temp_features_dir(tmp_path: Path) -> Path:
    """
    Create a temporary directory with a few fake features and labels.tsv files.

    This is used to test feature discovery / load behavior without touching real project files.
    """
    # Create core feature
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "meta.json").write_text('{"feature_name": "core"}', encoding="utf-8")
    (core_dir / "labels.tsv").write_text(
        "label\tde\ten\n"
        "core.save\tSpeichern\tSave\n"
        "core.cancel\tAbbrechen\tCancel\n",
        encoding="utf-8",
    )

    # Create authenticator feature
    auth_dir = tmp_path / "authenticator"
    auth_dir.mkdir()
    (auth_dir / "meta.json").write_text('{"feature_name": "authenticator"}', encoding="utf-8")
    (auth_dir / "labels.tsv").write_text(
        "label\tde\ten\n"
        "auth.login\tAnmelden\tLogin\n",
        encoding="utf-8",
    )

    # Create user_management feature
    user_dir = tmp_path / "user_management"
    user_dir.mkdir()
    (user_dir / "meta.json").write_text('{"feature_name": "user_management"}', encoding="utf-8")
    (user_dir / "labels.tsv").write_text(
        "label\tde\ten\n"
        "user.create\tErstellen\tCreate\n",
        encoding="utf-8",
    )

    # Create feature without labels.tsv (should be skipped by discovery)
    incomplete_dir = tmp_path / "incomplete"
    incomplete_dir.mkdir()
    (incomplete_dir / "meta.json").write_text('{"feature_name": "incomplete"}', encoding="utf-8")

    return tmp_path


@pytest.fixture
def feature_discovery_service(temp_features_dir: Path) -> FeatureDiscoveryService:
    """Feature discovery service configured to scan the temp feature directory."""
    # Tests expect FeatureDiscoveryService(features_root=...)
    return FeatureDiscoveryService(features_root=temp_features_dir)


@pytest.fixture
def mock_user_service() -> Mock:
    """
    Mocked UserManagementService.

    We intentionally do NOT instantiate UserDTO directly. Instead we create mocks with UserDTO spec
    and set required attributes. This makes tests resilient against UserDTO constructor changes.
    """
    mock_service = Mock()

    def _make_user(user_id: int, username: str, email: str, role: SystemRole, status: UserStatus) -> Mock:
        u = Mock(spec=UserDTO)
        u.id = user_id
        u.username = username
        u.email = email
        u.role = role
        u.status = status
        return u

    admin_user = _make_user(1, "admin", "admin@test.com", SystemRole.ADMIN, UserStatus.ACTIVE)
    qmb_user = _make_user(2, "qmb", "qmb@test.com", SystemRole.QMB, UserStatus.ACTIVE)
    regular_user = _make_user(3, "user", "user@test.com", SystemRole.USER, UserStatus.ACTIVE)

    def get_user_by_id(user_id: int):
        users = {1: admin_user, 2: qmb_user, 3: regular_user}
        return users.get(user_id)

    mock_service.get_user_by_id.side_effect = get_user_by_id
    return mock_service


@pytest.fixture
def translation_policy(mock_user_service: Mock) -> TranslationPolicy:
    """TranslationPolicy using the mocked user service."""
    return TranslationPolicy(user_service=mock_user_service)


@pytest.fixture
def translation_service(
    populated_repository: InMemoryTranslationRepository,
    translation_policy: TranslationPolicy,
    feature_discovery_service: FeatureDiscoveryService,
) -> TranslationService:
    """TranslationService wired with repo + policy + feature discovery."""
    return TranslationService(
        repository=populated_repository,
        policy=translation_policy,
        feature_discovery_service=feature_discovery_service,
    )


@pytest.fixture
def admin_user_dto() -> Mock:
    """Fixture providing an admin-like user object (UserDTO spec)."""
    u = Mock(spec=UserDTO)
    u.id = 1
    u.username = "admin"
    u.email = "admin@test.com"
    u.role = SystemRole.ADMIN
    u.status = UserStatus.ACTIVE
    return u


@pytest.fixture
def qmb_user_dto() -> Mock:
    """Fixture providing a QMB-like user object (UserDTO spec)."""
    u = Mock(spec=UserDTO)
    u.id = 2
    u.username = "qmb"
    u.email = "qmb@test.com"
    u.role = SystemRole.QMB
    u.status = UserStatus.ACTIVE
    return u


@pytest.fixture
def regular_user_dto() -> Mock:
    """Fixture providing a regular user object (UserDTO spec)."""
    u = Mock(spec=UserDTO)
    u.id = 3
    u.username = "user"
    u.email = "user@test.com"
    u.role = SystemRole.USER
    u.status = UserStatus.ACTIVE
    return u


# ---------------------------------------------------------------------------
# Aliases expected by tests
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user(admin_user_dto: Mock) -> Mock:
    """Alias fixture: tests expect 'admin_user'."""
    return admin_user_dto


@pytest.fixture
def qmb_user(qmb_user_dto: Mock) -> Mock:
    """Alias fixture: tests expect 'qmb_user'."""
    return qmb_user_dto


@pytest.fixture
def regular_user(regular_user_dto: Mock) -> Mock:
    """Alias fixture: tests expect 'regular_user'."""
    return regular_user_dto


# ---------------------------------------------------------------------------
# Temporary TSV file fixture expected by repository tests
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_tsv_file(tmp_path: Path) -> str:
    """
    Some repository tests expect a ready-to-use temp TSV path fixture named 'temp_tsv_file'.
    Returns:
        Absolute path as string (works with Path(...) in repository code).
    """
    p = tmp_path / "temp_labels.tsv"
    p.write_text(
        "label\tde\ten\n"
        "core.save\tSpeichern\tSave\n"
        "core.cancel\tAbbrechen\tCancel\n"
        "core.missing\tFehlt\t\n",
        encoding="utf-8",
    )
    return str(p)
