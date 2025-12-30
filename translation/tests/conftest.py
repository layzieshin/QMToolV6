from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from translation import FeatureDescriptor, reset_state


@pytest.fixture(autouse=True)
def _reset_translation_state():
    """Ensure a clean translation engine before each test."""
    reset_state()
    yield
    reset_state()


@pytest.fixture
def feature_factory(tmp_path: Path) -> Callable[[str, str], FeatureDescriptor]:
    """
    Helper to create a feature directory with a given labels.tsv content.
    Returns a FeatureDescriptor suitable for load_features.
    """

    def _create(feature_id: str, labels_content: str) -> FeatureDescriptor:
        root = tmp_path / feature_id
        root.mkdir(parents=True, exist_ok=True)
        (root / "labels.tsv").write_text(labels_content, encoding="utf-8")
        return FeatureDescriptor(id=feature_id, root_path=root)

    return _create
