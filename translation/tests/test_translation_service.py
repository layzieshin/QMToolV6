# tests/test_translation_service.py

def test_get_translation_success(translation_service, mock_repo):
    """Test successful translation retrieval."""
    # Arrange
    mock_repo.get_translation.return_value = TranslationDTO(
        label="core.save",
        language=SupportedLanguage.DE,
        text="Speichern",
        feature="core",
        status=TranslationStatus.COMPLETE
    )

    # Act
    result = translation_service.get("core. save", SupportedLanguage.DE, "core")

    # Assert
    assert result == "Speichern"


def test_get_translation_missing_logs_audit(translation_service, mock_audit):
    """Test missing translation triggers audit log."""
    # Arrange
    translation_service._repo.get_translation.return_value = None

    # Act
    result = translation_service.get(
        "missing.key",
        SupportedLanguage.EN,
        "test_feature",
        fallback_to_label=True
    )

    # Assert
    assert result == "missing.key"  # Fallback to label
    mock_audit.log.assert_called_once()
    call_details = mock_audit.log.call_args[1]["details"]
    assert call_details["event"] == "missing_translation"
    assert call_details["label"] == "missing.key"


def test_create_translation_requires_admin(translation_service, mock_policy):
    """Test policy enforcement for create operation."""
    # Arrange
    mock_policy.enforce_create.side_effect = TranslationPermissionError("Forbidden")
    dto = CreateTranslationDTO(
        label="new.key",
        feature="test",
        translations={SupportedLanguage.DE: "Text"}
    )

    # Act & Assert
    with pytest.raises(TranslationPermissionError):
        translation_service.create_translation(dto, actor_id=999)


def test_feature_discovery_finds_all_labels(discovery_service, tmp_path):
    """Test feature discovery scans correctly."""
    # Arrange: Create fake feature structure
    (tmp_path / "feature1" / "meta.json").write_text("{}")
    (tmp_path / "feature1" / "labels.tsv").write_text("label\tde\ten")
    (tmp_path / "feature2" / "meta.json").write_text("{}")
    (tmp_path / "feature2" / "labels.tsv").write_text("label\tde\ten")

    discovery = FeatureDiscoveryService(tmp_path)

    # Act
    discovered = discovery.discover_features()

    # Assert
    assert len(discovered) == 2
    assert "feature1" in discovered
    assert "feature2" in discovered