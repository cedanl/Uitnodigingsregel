"""Tests for settings module."""

from uitnodigingsregel.settings import load_settings


def test_load_settings_default() -> None:
    settings = load_settings()
    assert "dropout_column" in settings
    assert "random_seed" in settings
    assert settings["dropout_column"] == "Dropout"
