"""Package management for Zoya Studio."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from zoya_studio.core.config import Config


@dataclass
class Package:
    """Package information."""
    name: str
    version: str = "0.0.0"
    description: str = ""
    author: str = ""
    installed: bool = False
    latest: str = ""
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "installed": self.installed,
            "latest": self.latest,
            "dependencies": self.dependencies,
        }


class PackageManager:
    """Manages packages for Zoya projects."""

    def __init__(self, app: Any):
        self.app = app
        self.config = app.config if hasattr(app, "config") else Config.load()
        self.registry_url = self.config.packages.registry
        self.cache_dir = Path(self.config.packages.cache_dir or (
            Path.home() / ".zoya" / "studio" / "packages"
        ))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_project_manifest(self, project_path: str) -> dict[str, Any] | None:
        """Read project manifest (zoya.toml)."""
        manifest = Path(project_path) / "zoya.toml"
        if not manifest.exists():
            return None

        # Simple TOML-like parsing
        data: dict[str, Any] = {}
        current_section = ""

        for line in manifest.read_text(encoding="utf-8").split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                data[current_section] = {}
            elif "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if current_section:
                    data[current_section][key] = value
                else:
                    data[key] = value

        return data

    def save_project_manifest(self, project_path: str, data: dict[str, Any]) -> bool:
        """Save project manifest."""
        manifest = Path(project_path) / "zoya.toml"
        lines: list[str] = []

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"[{key}]")
                for k, v in value.items():
                    if isinstance(v, list):
                        v = "[" + ", ".join(f'"{x}"' for x in v) + "]"
                    elif isinstance(v, str):
                        v = f'"{v}"'
                    lines.append(f"{k} = {v}")
                lines.append("")
            else:
                if isinstance(value, str):
                    value = f'"{value}"'
                lines.append(f"{key} = {value}")

        try:
            manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return True
        except OSError:
            return False

    def list_installed(self, project_path: str | None = None) -> list[Package]:
        """List installed packages."""
        packages: list[Package] = []

        # System packages via pip
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for pkg in data:
                    packages.append(Package(
                        name=pkg["name"],
                        version=pkg["version"],
                        installed=True,
                        latest=pkg["version"],
                    ))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass

        return packages

    def list_dependencies(self, project_path: str) -> list[Package]:
        """List project dependencies from manifest."""
        manifest = self.get_project_manifest(project_path)
        if not manifest or "dependencies" not in manifest:
            return []

        deps = manifest["dependencies"]
        packages: list[Package] = []

        for name, version in deps.items():
            packages.append(Package(
                name=name,
                version=version if isinstance(version, str) else str(version),
                installed=True,
            ))

        return packages

    def install(self, name: str, version: str | None = None,
                project_path: str | None = None) -> tuple[bool, str]:
        """Install a package."""
        version_spec = f"=={version}" if version else ""

        try:
            result = subprocess.run(
                ["pip", "install", f"{name}{version_spec}"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                if project_path:
                    self._add_dependency(project_path, name, version or "latest")
                return True, f"Installed {name}"
            else:
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except FileNotFoundError:
            return False, "pip not found"

    def uninstall(self, name: str, project_path: str | None = None) -> tuple[bool, str]:
        """Uninstall a package."""
        try:
            result = subprocess.run(
                ["pip", "uninstall", "-y", name],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                if project_path:
                    self._remove_dependency(project_path, name)
                return True, f"Uninstalled {name}"
            else:
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Uninstall timed out"
        except FileNotFoundError:
            return False, "pip not found"

    def update(self, name: str | None = None) -> tuple[bool, str]:
        """Update packages."""
        if name:
            try:
                result = subprocess.run(
                    ["pip", "install", "--upgrade", name],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode == 0:
                    return True, f"Updated {name}"
                return False, result.stderr
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                return False, str(e)
        else:
            try:
                result = subprocess.run(
                    ["pip", "list", "--outdated", "--format=json"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    outdated = json.loads(result.stdout)
                    names = [p["name"] for p in outdated]
                    if not names:
                        return True, "All packages up to date"
                    result = subprocess.run(
                        ["pip", "install", "--upgrade", *names],
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    if result.returncode == 0:
                        return True, f"Updated {len(names)} packages"
                    return False, result.stderr
                return False, result.stderr
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
                return False, str(e)

    def search(self, query: str) -> list[Package]:
        """Search packages in registry."""
        # This would query the registry; for now simulate
        return [
            Package(
                name=f"{query}-core",
                version="1.0.0",
                description=f"Core package for {query}",
                installed=False,
            ),
            Package(
                name=f"{query}-utils",
                version="0.5.0",
                description=f"Utility functions for {query}",
                installed=False,
            ),
            Package(
                name=f"zoya-{query}",
                version="2.1.0",
                description=f"Zoya integration for {query}",
                installed=False,
            ),
        ]

    def get_info(self, name: str) -> Package | None:
        """Get package info."""
        try:
            result = subprocess.run(
                ["pip", "show", name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                info: dict[str, str] = {}
                for line in result.stdout.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        info[key.strip()] = value.strip()

                return Package(
                    name=info.get("Name", name),
                    version=info.get("Version", ""),
                    description=info.get("Summary", ""),
                    author=info.get("Author", ""),
                    installed=True,
                    latest=info.get("Version", ""),
                )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def _add_dependency(self, project_path: str, name: str, version: str) -> None:
        """Add dependency to manifest."""
        manifest = self.get_project_manifest(project_path)
        if manifest is None:
            manifest = {"project": {}, "dependencies": {}}

        if "dependencies" not in manifest:
            manifest["dependencies"] = {}

        manifest["dependencies"][name] = version

        project_name = Path(project_path).name
        manifest["project"]["name"] = manifest["project"].get("name", project_name)

        self.save_project_manifest(project_path, manifest)

    def _remove_dependency(self, project_path: str, name: str) -> None:
        """Remove dependency from manifest."""
        manifest = self.get_project_manifest(project_path)
        if not manifest or "dependencies" not in manifest:
            return

        if name in manifest["dependencies"]:
            del manifest["dependencies"][name]
            self.save_project_manifest(project_path, manifest)
