"""
Feature Discovery Service
==========================

Discovers features with translation files (labels.tsv).

This is a REPOSITORY helper, not a business service.
It scans the project directory for features with meta.json and labels.tsv.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, List


class FeatureDiscoveryService:
    """
    Discovers all features with labels.tsv files.

    Discovery logic:
    ----------------
    1. Scan features root for directories with meta.json
    2. Check if <feature_dir>/labels.tsv exists
    3. Return list of tuples (feature_name, labels_path_or_None)

    Expected structure:
    -------------------
        authenticator/
        ├── meta.json
        └── labels.tsv

        user_management/
        ├── meta.json
        └── labels.tsv

    IMPORTANT:
    ----------
    The test-suite constructs this class with:
        FeatureDiscoveryService(features_root=...)

    Your previous implementation accepted only "project_root" and also
    referenced "self.features_root" without defining it.
    This file fixes both issues and keeps backwards compatibility.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        *,
        features_root: Optional[Path] = None,
    ):
        """
        Initialize discovery service.

        Args:
            project_root: Backwards-compatible alias (older code)
            features_root: Root directory to scan (used by tests/fixtures)
        """
        # Tests use "features_root=...". If not provided, fall back to project_root or cwd.
        root = features_root or project_root or Path.cwd()
        self.features_root: Path = Path(root)

    def discover_features(self) -> List[Tuple[str, Optional[str]]]:
        """
        Returns list of tuples (feature_name, labels_path_or_None).
        """
        if not self.features_root.exists():
            return []

        features: List[Tuple[str, Optional[str]]] = []

        for child in self.features_root.iterdir():
            if not child.is_dir():
                continue

            meta = child / "meta.json"
            if not meta.exists():
                continue

            # Try to read "feature_name" from meta.json, fallback to directory name
            try:
                import json

                data = json.loads(meta.read_text(encoding="utf-8"))
                fname = data.get("feature_name", child.name)
            except Exception:
                fname = child.name

            labels = child / "labels.tsv"
            labels_path = str(labels) if labels.exists() else None
            features.append((fname, labels_path))

        return features

    def get_feature_tsv_path(self, feature_name: str) -> Optional[Path]:
        """
        Get path to labels.tsv for a specific feature.

        Args:
            feature_name: Name of the feature (directory name)

        Returns:
            Path if found, None otherwise
        """
        feature_dir = self.features_root / feature_name
        labels_file = feature_dir / "labels.tsv"
        return labels_file if labels_file.exists() else None

    def validate_tsv_format(self, tsv_path: Path) -> tuple[bool, Optional[str]]:
        """
        Validate TSV file format without loading.

        Args:
            tsv_path: Path to TSV file

        Returns:
            (is_valid, error_message) tuple
        """
        if not tsv_path.exists():
            return False, f"File not found: {tsv_path}"

        try:
            import csv

            with tsv_path.open(encoding="utf-8") as f:
                reader = csv.reader(f, delimiter="\t")
                header = next(reader)

                if not header or header[0] != "label":
                    return (
                        False,
                        f"Invalid header: expected 'label', got '{header[0] if header else 'empty'}'",
                    )

                # Check language columns
                from translation.enum.translation_enum import SupportedLanguage

                for col in header[1:]:
                    try:
                        SupportedLanguage.from_string(col)
                    except ValueError:
                        return False, f"Unsupported language in header: {col}"

                return True, None

        except Exception as e:
            return False, f"Failed to read TSV: {str(e)}"
