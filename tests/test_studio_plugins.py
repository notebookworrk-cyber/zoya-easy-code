"""Tests for Zoya Studio plugin system."""

import json
import tempfile
from pathlib import Path

from zoya_studio.core.config import Config
from zoya_studio.plugins import PluginManager, PluginInfo, BasePlugin


class FakeApp:
    def __init__(self):
        self.config = Config()
        self.config.plugins.enabled = True
        self.config.plugins.auto_load = False

    def log(self, msg):
        pass


class TestPlugin(BasePlugin):
    name = "test-plugin"
    version = "1.0.0"
    description = "Test plugin"

    def activate(self):
        self.register_command("hello", self.cmd_hello)

    def deactivate(self):
        self.unregister_command("hello")

    def cmd_hello(self, args):
        return "Hello from plugin!"


def test_plugin_manager_discover_empty():
    """Test discovering plugins in empty dir."""
    with tempfile.TemporaryDirectory() as tmp:
        app = FakeApp()
        app.config.plugins.directory = tmp
        pm = PluginManager(app)
        plugins = pm.discover_plugins()
        assert plugins == []


def test_plugin_manager_install_and_load():
    """Test installing and loading a plugin."""
    with tempfile.TemporaryDirectory() as tmp:
        app = FakeApp()
        app.config.plugins.directory = tmp

        # Create plugin files
        plugin_dir = Path(tmp) / "myplugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "myplugin",
                    "version": "0.1.0",
                    "description": "Test",
                    "author": "tester",
                    "entry": "plugin.py",
                    "permissions": ["ui"],
                }
            )
        )
        (plugin_dir / "plugin.py").write_text("""
from zoya_studio.plugins.base import BasePlugin

class Plugin(BasePlugin):
    name = "myplugin"
    version = "0.1.0"
    description = "Test"

    def activate(self):
        self.register_command("ping", self.ping)

    def deactivate(self):
        self.unregister_command("ping")

    def ping(self, *args):
        return "pong"
""")

        pm = PluginManager(app)
        plugins = pm.discover_plugins()
        assert len(plugins) == 1
        assert plugins[0].name == "myplugin"

        # Load plugin
        info = plugins[0]
        assert pm.load_plugin(info)
        assert "ping" in pm.commands
        assert pm.execute_command("ping") == "pong"

        # Unload
        assert pm.unload_plugin("myplugin")
        assert "ping" not in pm.commands


def test_plugin_base_class():
    """Test BasePlugin abstract methods."""
    import pytest

    with pytest.raises(TypeError):
        BasePlugin(FakeApp())
