"""Tests for SettingsManager."""

import json
import os
import pytest

from src.core.settings import SettingsManager


@pytest.fixture()
def settings_path(tmp_path):
    """Return a temporary settings file path and patch SettingsManager."""
    path = tmp_path / "test_webcap_settings.json"
    original = SettingsManager.SETTINGS_FILE
    SettingsManager.SETTINGS_FILE = str(path)
    yield str(path)
    SettingsManager.SETTINGS_FILE = original


def test_default_settings(settings_path):
    """load_settings() with no file returns DEFAULT_SETTINGS."""
    assert not os.path.exists(settings_path)
    settings = SettingsManager.load_settings()
    assert settings == SettingsManager.DEFAULT_SETTINGS


def test_save_and_load(settings_path):
    """Saved settings can be loaded back with the same values."""
    custom = dict(SettingsManager.DEFAULT_SETTINGS)
    custom["start_delay"] = 5
    custom["resolution"] = "1920x1080"
    SettingsManager.save_settings(custom)
    loaded = SettingsManager.load_settings()
    assert loaded["start_delay"] == 5
    assert loaded["resolution"] == "1920x1080"


def test_load_corrupted_file(settings_path):
    """A corrupted JSON file causes load_settings() to fall back to defaults."""
    with open(settings_path, "w") as f:
        f.write("{ this is not valid json !!!")
    settings = SettingsManager.load_settings()
    assert settings == SettingsManager.DEFAULT_SETTINGS


def test_load_partial_settings(settings_path):
    """Partial settings file is merged with defaults; missing keys come from defaults."""
    partial = {"start_delay": 10}
    with open(settings_path, "w") as f:
        json.dump(partial, f)
    settings = SettingsManager.load_settings()
    assert settings["start_delay"] == 10
    # Keys not in the partial file should come from defaults
    assert settings["resolution"] == SettingsManager.DEFAULT_SETTINGS["resolution"]
    assert "auto_stop_enabled" in settings


def test_default_has_auto_stop_enabled():
    """DEFAULT_SETTINGS must contain auto_stop_enabled with a default of False."""
    assert "auto_stop_enabled" in SettingsManager.DEFAULT_SETTINGS
    assert SettingsManager.DEFAULT_SETTINGS["auto_stop_enabled"] is False
