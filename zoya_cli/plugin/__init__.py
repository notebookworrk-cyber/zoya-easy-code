"""Plugin system for the Zoya CLI.

Plugins are Python packages installed via pip or loaded from a local path.
Each plugin exposes a ``zoya_plugin`` entry point group that can register
additional commands in the global registry.
"""

from __future__ import annotations

import importlib
import importlib.metadata
from pathlib import Path
from typing import Dict, List

from zoya_cli.core.registry import registry
from zoya_cli.core.errors import PluginError

INSTALLED_PLUGINS_DIR = Path.home() / ".zoya" / "plugins"


class PluginManager:
    """Manages the lifecycle of CLI plugins."""

    def __init__(self) -> None:
        self._loaded: set[str] = set()

    def discover(self) -> list[str]:
        plugins: list[str] = []
        for ep in importlib.metadata.entry_points(group="zoya_plugin"):
            if ep.name not in self._loaded:
                plugins.append(ep.name)
        return plugins

    def load(self, name: str) -> bool:
        if name in self._loaded:
            return False
        try:
            dist = importlib.metadata.distribution(name)
            ep = next((e for e in dist.entry_points if e.group == "zoya_plugin"), None)
            if not ep:
                raise PluginError(f"No 'zoya_plugin' entry point in `{name}`.")
            parts = ep.value.split(":")
            module_name = parts[0]
            attr_name = parts[1] if len(parts) > 1 else "register_plugin"
            module = importlib.import_module(module_name)
            if hasattr(module, attr_name):
                getattr(module, attr_name)(registry)
            self._loaded.add(name)
            return True
        except (importlib.metadata.PackageNotFoundError, ImportError, AttributeError) as exc:
            raise PluginError(f"Failed to load plugin `{name}`", cause=exc)

    def load_all(self) -> list[str]:
        loaded: list[str] = []
        for name in self.discover():
            try:
                self.load(name)
                loaded.append(name)
            except PluginError:
                pass
        return loaded

    def is_loaded(self, name: str) -> bool:
        return name in self._loaded

    def unload_all(self) -> None:
        self._loaded.clear()

    def list(self) -> list[dict]:
        result: list[dict] = []
        for name in self.discover():
            result.append(
                {
                    "name": name,
                    "loaded": name in self._loaded,
                    "commands": registry.plugin_commands(name),
                }
            )
        for name in self._loaded:
            if name not in {p["name"] for p in result}:
                result.append(
                    {"name": name, "loaded": True, "commands": registry.plugin_commands(name)}
                )
        return result


plugin_manager = PluginManager()
