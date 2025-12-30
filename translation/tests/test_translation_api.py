from pathlib import Path

import pytest

from translation import (
    available_languages,
    get_effective_language,
    load_features,
    set_global_language,
    set_user_language,
    t,
)


def test_tsv_parsing_and_duplicates(feature_factory, caplog):
    caplog.set_level("WARNING", logger="translation")
    descriptor = feature_factory(
        "authenticator",
        "\n".join(
            [
                "label\tde\ten",
                "# comment line",
                "",
                "login.button\tAnmelden\tLogin",
                "login.button\tAnmelden\tLogin",  # identical duplicate (ok)
                "login.button\tAnmeldung\tLogin",  # different duplicate -> log + last wins
                "empty.translation\t\t",
            ]
        ),
    )

    load_features([descriptor])

    assert t("login.button", feature_id="authenticator") == "Anmeldung"
    assert t("empty.translation", feature_id="authenticator") == "empty.translation"

    duplicate_logs = [rec for rec in caplog.records if getattr(rec, "action", "") == "I18N_DUPLICATE_KEY"]
    empty_logs = [rec for rec in caplog.records if getattr(rec, "action", "") == "I18N_EMPTY_TRANSLATION"]
    assert len(duplicate_logs) == 1
    assert len(empty_logs) == 1


def test_language_resolution_user_overrides_global(feature_factory):
    descriptor = feature_factory(
        "core",
        "label\tde\ten\n"
        "core.save\tSpeichern\tSave\n",
    )
    load_features([descriptor])

    set_global_language("en")
    set_user_language(5, "de")

    assert get_effective_language(None) == "en"
    assert t("core.save", feature_id="core", user_id=None) == "Save"
    assert t("core.save", feature_id="core", user_id=5) == "Speichern"


def test_missing_key_logged_once(feature_factory, caplog):
    caplog.set_level("WARNING", logger="translation")
    descriptor = feature_factory(
        "core",
        "label\tde\ten\n"
        "core.save\tSpeichern\tSave\n",
    )
    load_features([descriptor])

    assert t("missing.key", feature_id="core") == "missing.key"
    assert t("missing.key", feature_id="core") == "missing.key"

    missing_logs = [rec for rec in caplog.records if getattr(rec, "action", "") == "I18N_MISSING_KEY"]
    assert len(missing_logs) == 1


def test_feature_language_fallback_and_available_languages(feature_factory):
    feat_a = feature_factory(
        "authenticator",
        "label\tde\ten\n"
        "auth.login\tAnmelden\tLogin\n",
    )
    feat_b = feature_factory(
        "user_management",
        "label\tde\n"
        "user.create\tErstellen\n",
    )
    load_features([feat_a, feat_b])

    set_global_language("en")

    # Feature without EN falls back to key
    assert t("user.create", feature_id="user_management") == "user.create"

    # Available languages per feature
    assert available_languages("user_management") == ["de"]
    assert "en" in available_languages()


def test_missing_labels_file_logged(feature_factory, tmp_path, caplog):
    caplog.set_level("WARNING", logger="translation")

    # Create descriptor without labels.tsv
    root = tmp_path / "incomplete"
    root.mkdir(parents=True, exist_ok=True)
    descriptor = feature_factory("incomplete", "label\tde\nkey\tWert\n")
    # Remove the file to simulate missing
    Path(descriptor.root_path / "labels.tsv").unlink()

    load_features([descriptor])

    # No crash and fallback to key
    assert t("any.key", feature_id="incomplete") == "any.key"

    missing_logs = [rec for rec in caplog.records if getattr(rec, "action", "") == "I18N_MISSING_KEY"]
    assert missing_logs  # at least one log entry
