"""Tests for UIMetadataService."""
from pathlib import Path
import json

from configurator.repository.config_repository import ConfigRepository
from configurator.repository.feature_repository import FeatureRepository
from configurator.services.configurator_service import ConfiguratorService

from UI.services.ui_metadata_service import UIMetadataService


def test_metadata_service_loads_meta_and_labels(tmp_path: Path):
    feature_dir = tmp_path / "sample_feature"
    feature_dir.mkdir()
    meta = {
        "id": "sample_feature",
        "label": "Sample Feature",
        "version": "1.0.0",
        "main_class": "sample_feature.services.sample_service.SampleService",
    }
    (feature_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    labels_path = tmp_path / "labels.tsv"
    labels_path.write_text("label\tde\ten\ncore.save\tSpeichern\tSave\n", encoding="utf-8")

    feature_repo = FeatureRepository(features_root=str(tmp_path))
    config_repo = ConfigRepository(project_root=str(tmp_path))
    configurator = ConfiguratorService(feature_repo, config_repo)

    service = UIMetadataService(configurator, labels_path)
    meta_payload = service.load_meta_json()
    labels_payload = service.load_labels_tsv()

    assert "sample_feature" in meta_payload
    assert "Sample Feature" in meta_payload
    assert "core.save" in labels_payload
