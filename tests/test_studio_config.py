"""Tests for Zoya Studio configuration system."""

import json
import tempfile
from pathlib import Path

import pytest

from zoya_studio.core.config import Config, ThemeConfig, THEME_PRESETS


def test_config_defaults():
    """Test default config values."""
    config = Config()
    assert config.theme.name == "dark"
    assert config.ui.show_left_sidebar is True
    assert config.editor.tab_size == 4
    assert config.ai.provider == "openai"
    assert config.ai.temperature == 0.7


def test_config_save_load():
    """Test config save and load round trip."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        config = Config()
        config.ai.provider = "anthropic"
        config.ai.model = "claude-3"
        config.theme.name = "midnight"
        config.save(str(path))

        assert path.exists()

        loaded = Config.load(str(path))
        assert loaded.ai.provider == "anthropic"
        assert loaded.ai.model == "claude-3"
        assert loaded.theme.name == "midnight"


def test_config_get_set():
    """Test nested get/set."""
    config = Config()
    config.set("ai.provider", "ollama")
    assert config.get("ai.provider") == "ollama"
    config.set("editor.tab_size", 2)
    assert config.editor.tab_size == 2


def test_config_reset():
    """Test config reset."""
    config = Config()
    config.ai.provider = "gemini"
    config.reset()
    assert config.ai.provider == "openai"


def test_theme_presets():
    """Test theme presets exist."""
    assert "dark" in THEME_PRESETS
    assert "light" in THEME_PRESETS
    assert "midnight" in THEME_PRESETS
    assert "solarized" in THEME_PRESETS
    assert "dracula" in THEME_PRESETS

    for name, theme in THEME_PRESETS.items():
        assert isinstance(theme, ThemeConfig)
        assert theme.background.startswith("#")
        assert theme.primary.startswith("#")


def test_config_to_from_dict():
    """Test dict conversion."""
    config = Config()
    config.ai.provider = "mock"
    data = config.to_dict()
    assert isinstance(data, dict)
    assert data["ai"]["provider"] == "mock"

    config2 = Config.from_dict(data)
    assert config2.ai.provider == "mock"
