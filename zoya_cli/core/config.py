"""Configuration system for the Zoya CLI.

Supports two layers that are merged at runtime:

* **Global** configuration stored in ``~/.zoya/config.toml`` applies to every
  project and to commands run outside a project.
* **Project** configuration stored in ``<project>/zoya.toml`` overrides the
  global layer for the current project.

The merged view is exposed through :class:`Config` which also supports simple
dotted-path get/set operations and persistence.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Mapping

from zoya_cli.core.errors import ConfigError

GLOBAL_CONFIG_DIR = Path.home() / ".zoya"
GLOBAL_CONFIG_PATH = GLOBAL_CONFIG_DIR / "config.toml"
PROJECT_CONFIG_NAME = "zoya.toml"

DEFAULTS: dict[str, Any] = {
    "theme": "aurora",
    "ai": {
        "provider": "mock",
        "model": "auto",
        "temperature": 0.2,
        "max_tokens": 2048,
        "api_base": "",
        "api_key": "",
    },
    "build": {"target": "native", "optimize": True, "jobs": 0},
    "registry": {"url": "https://packages.zoya.dev", "offline": False},
    "templates": {"default": "console"},
    "terminal": {"color": "auto", "verbose": False, "quiet": False},
}


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` onto a copy of ``base``."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, Mapping):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _set_path(data: dict[str, Any], path: str, value: Any) -> None:
    """Set a value at a dotted path, creating intermediate dicts as needed."""
    parts = path.split(".")
    node = data
    for part in parts[:-1]:
        nxt = node.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            node[part] = nxt
        node = nxt
    node[parts[-1]] = value


def _get_path(data: Mapping[str, Any], path: str) -> Any:
    node: Any = data
    for part in path.split("."):
        if not isinstance(node, Mapping) or part not in node:
            raise KeyError(path)
        node = node[part]
    return node


class Config:
    """Merged view of global + project configuration."""

    def __init__(
        self, global_path: Path = GLOBAL_CONFIG_PATH, project_path: Path | None = None
    ) -> None:
        self.global_path = global_path
        self.project_path = project_path
        self._data = dict(DEFAULTS)
        self._load()

    # ------------------------------------------------------------------ load
    def _load(self) -> None:
        if self.global_path.exists():
            try:
                with self.global_path.open("rb") as fh:
                    g = tomllib.load(fh)
                self._data = _deep_merge(self._data, g)
            except (tomllib.TOMLDecodeError, OSError) as exc:
                raise ConfigError(
                    f"Could not read global config {self.global_path}",
                    hints=["Run 'zoya doctor' to diagnose configuration issues."],
                    cause=exc,
                )
        if self.project_path and self.project_path.exists():
            try:
                with self.project_path.open("rb") as fh:
                    p = tomllib.load(fh)
                self._data = _deep_merge(self._data, p)
            except (tomllib.TOMLDecodeError, OSError) as exc:
                raise ConfigError(
                    f"Could not read project config {self.project_path}",
                    hints=["Check the file for invalid TOML syntax."],
                    cause=exc,
                )

    # ----------------------------------------------------------------- query
    def get(self, path: str, default: Any = None) -> Any:
        try:
            return _get_path(self._data, path)
        except KeyError:
            return default

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)

    # --------------------------------------------------------------- mutation
    @property
    def global_config_dir(self) -> Path:
        return self.global_path.parent

    def set_global(self, path: str, value: Any) -> None:
        """Set a value in the *global* config and persist it."""
        data = self._read_file(self.global_path)
        _set_path(data, path, value)
        self._write_file(self.global_path, data)
        self._load()

    def set_project(self, path: str, value: Any) -> None:
        """Set a value in the *project* config and persist it."""
        if not self.project_path:
            raise ConfigError(
                "No Zoya project found in the current directory.",
                hints=["Run 'zoya init' to create a project."],
            )
        data = self._read_file(self.project_path)
        _set_path(data, path, value)
        self._write_file(self.project_path, data)
        self._load()

    # ------------------------------------------------------------- persistence
    def _read_file(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("rb") as fh:
            return tomllib.load(fh)

    def _write_file(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            fh.write(_dump_toml(data))


def _dump_toml(data: Mapping[str, Any], indent: int = 0) -> str:
    """Minimal TOML serializer for the configuration values we emit."""
    pad = "  " * indent
    lines: list[str] = []
    # Scalars first, then tables, for readable output.
    scalars: list[str] = []
    tables: list[tuple[str, Any]] = []
    for key, value in data.items():
        if isinstance(value, Mapping):
            tables.append((key, value))
        else:
            scalars.append(_toml_scalar(key, value))
    for line in scalars:
        lines.append(pad + line)
    for key, value in tables:
        lines.append(f"\n{pad}[{key}]")
        lines.append(_dump_toml(value, indent + 0).rstrip("\n"))
    return "\n".join(lines) + "\n"


def _toml_scalar(key: str, value: Any) -> str:
    if isinstance(value, bool):
        return f"{key} = {'true' if value else 'false'}"
    if isinstance(value, (int, float)):
        return f"{key} = {value}"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'{key} = "{escaped}"'
    if isinstance(value, (list, tuple)):
        inner = ", ".join(_toml_literal(v) for v in value)
        return f"{key} = [{inner}]"
    return f'{key} = "{value}"'


def _toml_literal(value: Any) -> str:
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return f'"{value}"'


def find_project_root(start: Path | None = None) -> Path | None:
    """Walk upward looking for a ``zoya.toml`` project marker."""
    cur = (start or Path.cwd()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / PROJECT_CONFIG_NAME).exists():
            return candidate
    return None
