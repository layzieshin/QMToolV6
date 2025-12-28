from pathlib import Path
from typing import Optional


class FeatureDiscoveryService:
    """
    Discovers all features with labels.tsv files.

    Discovery logic:
    1. Scan project root for directories with meta.json
    2. Check if <feature_dir>/labels.tsv exists
    3. Return list of discovered features

    Expected structure:
        authenticator/
        ├── meta.json
        └── labels. tsv

        user_management/
        ├── meta.json
        └── labels.tsv
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Args:
            project_root: Root directory to scan (defaults to cwd)
        """
        self._root = project_root or Path.cwd()

    def discover_features(self) -> dict[str, Path]:
        """
        Discover all features with labels.tsv.

        Returns:
            {"authenticator": Path("/path/to/authenticator/labels. tsv"), ...}
        """
        discovered = {}

        for item in self._root.iterdir():
            if not item.is_dir():
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

        Returns:
            Path if found, None otherwise
        """
        feature_dir = self._root / feature_name
        labels_file = feature_dir / "labels.tsv"

        return labels_file if labels_file.exists() else None