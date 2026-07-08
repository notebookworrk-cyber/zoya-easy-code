"""Plugin system for Zoya Studio."""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from zoya_studio.core.config import Config
from zoya_studio.plugins.base import BasePlugin

__all__ = ["PluginManager", "PluginInfo", "BasePlugin"]


@dataclass
class PluginInfo:
    """Plugin metadata."""

    name: str
    version: str
    description: str
    author: str
    entry: str
    permissions: list[str] = field(default_factory=list)
    enabled: bool = True
    path: str = ""


class PluginManager:
    """Manages plugins."""

    def __init__(self, app: Any):
        self.app = app
        self.config = app.config if hasattr(app, "config") else Config.load()
        self.plugins_dir = Path(
            self.config.plugins.directory or (Path.home() / ".zoya" / "studio" / "plugins")
        )
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.plugins: dict[str, BasePlugin] = {}
        self.plugin_info: dict[str, PluginInfo] = {}
        self.commands: dict[str, Callable] = {}

    def discover_plugins(self) -> list[PluginInfo]:
        """Discover available plugins."""
        discovered: list[PluginInfo] = []

        if not self.plugins_dir.exists():
            return discovered

        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            manifest = plugin_dir / "plugin.json"
            if not manifest.exists():
                continue

            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                info = PluginInfo(
                    name=data.get("name", plugin_dir.name),
                    version=data.get("version", "0.0.0"),
                    description=data.get("description", ""),
                    author=data.get("author", ""),
                    entry=data.get("entry", "plugin.py"),
                    permissions=data.get("permissions", []),
                    path=str(plugin_dir),
                )
                discovered.append(info)
                self.plugin_info[info.name] = info
            except (json.JSONDecodeError, OSError):
                continue

        return discovered

    def load_plugin(self, info: PluginInfo) -> bool:
        """Load a plugin."""
        if not self.config.plugins.enabled:
            return False

        entry_path = Path(info.path) / info.entry
        if not entry_path.exists():
            return False

        try:
            spec = importlib.util.spec_from_file_location(
                f"zoya_plugin_{info.name}",
                str(entry_path),
            )
            if spec is None or spec.loader is None:
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, "Plugin"):
                return False

            plugin_class = getattr(module, "Plugin")
            plugin = plugin_class(self.app)
            plugin.activate()

            self.plugins[info.name] = plugin

            for cmd_name, handler in plugin._commands.items():
                self.commands[cmd_name] = handler

            return True
        except Exception as e:
            if hasattr(self.app, "log"):
                self.app.log(f"Failed to load plugin {info.name}: {e}")
            return False

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin."""
        if name not in self.plugins:
            return False

        plugin = self.plugins[name]
        cmd_names = list(plugin._commands.keys())
        plugin.deactivate()

        for cmd_name in cmd_names:
            self.commands.pop(cmd_name, None)

        del self.plugins[name]
        return True

    def load_all(self) -> None:
        """Load all discovered plugins."""
        if not self.config.plugins.auto_load:
            return

        for info in self.discover_plugins():
            if info.enabled:
                self.load_plugin(info)

    def execute_command(self, name: str, *args: Any) -> Any:
        """Execute a plugin command."""
        if name in self.commands:
            return self.commands[name](*args)
        return None

    def install_plugin(self, source: str) -> bool:
        """Install a plugin from source."""
        source_path = Path(source)
        if not source_path.exists():
            return False

        if source_path.is_file() and source_path.suffix == ".zip":
            import zipfile

            with zipfile.ZipFile(source_path) as zf:
                zf.extractall(self.plugins_dir)
            return True
        elif source_path.is_dir():
            dest = self.plugins_dir / source_path.name
            import shutil

            shutil.copytree(source_path, dest, dirs_exist_ok=True)
            return True

        return False

    def uninstall_plugin(self, name: str) -> bool:
        """Uninstall a plugin."""
        if name in self.plugin_info:
            info = self.plugin_info[name]
            import shutil

            shutil.rmtree(info.path, ignore_errors=True)
            self.plugin_info.pop(name, None)
            self.unload_plugin(name)
            return True
        return False

    def list_plugins(self) -> list[PluginInfo]:
        """List all plugins."""
        if not self.plugin_info:
            self.discover_plugins()
        return list(self.plugin_info.values())

    def get_plugin(self, name: str) -> BasePlugin | None:
        """Get loaded plugin instance."""
        return self.plugins.get(name)
