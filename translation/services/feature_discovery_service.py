"""
Feature Discovery Service
==========================

Discovers features with translation files (labels.tsv).

This is a REPOSITORY helper, not a business service.
It scans the project directory for features with meta. json and labels.tsv.
"""

from pathlib import Path
from typing import Dict, Optional


class FeatureDiscoveryService:
    """
    Discovers all features with labels.tsv files. 

    Discovery logic:
    ----------------
    1. Scan project root for directories with meta.json
    2. Check if <feature_dir>/labels.tsv exists
    3. Return mapping of feature_name -> tsv_path

    Expected structure:
    -------------------
        authenticator/
        ├── meta.json
        └── labels.tsv

        user_management/
        ├── meta.json
        └── labels.tsv

    Usage:
    ------
        >>> discovery = FeatureDiscoveryService()
        >>> features = discovery.discover_features()
        >>> features
        {'authenticator': Path('. ../authenticator/labels.tsv'), ...}
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize discovery service.

        Args:
            project_root: Root directory to scan (defaults to cwd)
        """
        self._root = project_root or Path.cwd()

    def discover_features(self) -> Dict[str, Path]:
        """
        Discover all features with labels.tsv. 

        Returns:
            Dict mapping feature_name to labels.tsv Path

        Example:
        --------
            >>> discovery = FeatureDiscoveryService()
            >>> features = discovery.discover_features()
            >>> 'authenticator' in features
            True
        """
        discovered = {}

        for item in self._root.iterdir():
            if not item.is_dir():
                continue

            # Skip hidden directories and special dirs
            if item.name.startswith(". ") or item.name.startswith("__"):
                continue

            # Check for meta.json (feature marker)
            meta_file = item / "meta.json"
            if not meta_file.exists():
                continue

            # Check for labels.tsv
            labels_file = item / "labels.tsv"
            if labels_file.exists():
                discovered[item.name] = labels_file

        return discovered

    def get_feature_tsv_path(self, feature_name: str) -> Optional[Path]:
        """
        Get path to labels.tsv for a specific feature.

        Args:
            feature_name: Name of the feature

        Returns:
            Path if found, None otherwise

        Example:
        --------
            >>> discovery = FeatureDiscoveryService()
            >>> path = discovery.get_feature_tsv_path("authenticator")
            >>> path.exists()
            True
        """
        feature_dir = self._root / feature_name
        labels_file = feature_dir / "labels.tsv"

        return labels_file if labels_file.exists() else None

    def validate_tsv_format(self, tsv_path: Path) -> tuple[bool, Optional[str]]:
        """
        Validate TSV file format without loading.

        Args:
            tsv_path: Path to TSV file

        Returns:
            (is_valid, error_message) tuple

        Example:
        --------
            >>> valid, error = discovery.validate_tsv_format(Path("labels.tsv"))
            >>> valid
            True
        """
        if not tsv_path.exists():
            return False, f"File not found: {tsv_path}"

        try:
            import csv
            with tsv_path.open(encoding="utf-8") as f:
                reader = csv.reader(f, delimiter="\t")
                header = next(reader)

                if not header or header[0] != "label":
                    return False, f"Invalid header: expected 'label', got '{header[0] if header else 'empty'}'"

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