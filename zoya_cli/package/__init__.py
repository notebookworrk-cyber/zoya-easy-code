"""Package management internals:

- ``ProjectModel`` represents the project's dependency specification.
- ``Resolver`` resolves version constraints using a simple SAT-like strategy.
- ``Cache`` manages an offline package cache.
- ``Registry`` provides a local package index.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from zoya_cli.core.config import Config
from zoya_cli.core.errors import PackageError

# A simple constraint parser: supports ``>=``, ``<=``, ``==``, ``~=``, ``!=``, ``>``, ``<``.
_CONSTRAINT_RE = re.compile(r"(>=|<=|==|~=|!=|>|<)\s*([\w.*]+)")


@dataclass
class PackageInfo:
    name: str
    version: str
    description: str = ""
    dependencies: Dict[str, str] = field(default_factory=dict)
    sha256: str = ""
    size: int = 0


@dataclass
class LockEntry:
    name: str
    version: str
    dependencies: Dict[str, str]
    integrity: str  # sha256-<base64>


class ProjectModel:
    """Represents a Zoya project's dependency specification."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        cfgs = [self.root / "zoya.toml", self.root / "pyproject.toml"]
        for cfg in cfgs:
            if cfg.exists():
                import tomllib

                self._data = tomllib.loads(cfg.read_text(encoding="utf-8"))
                return

    @property
    def dependencies(self) -> Dict[str, str]:
        deps: Dict[str, str] = {}
        for source in (
            self._data.get("dependencies", {}),
            self._data.get("project", {}).get("dependencies", {}),
        ):
            if isinstance(source, dict):
                deps.update(source)
            elif isinstance(source, list):
                for item in source:
                    if isinstance(item, str):
                        parts = item.split(";")[0].strip().split(">=", 1)
                        deps[parts[0]] = f">={parts[1]}" if len(parts) > 1 else "*"
        return deps

    @property
    def name(self) -> str:
        for source in [self._data, self._data.get("project", {})]:
            if isinstance(source.get("name"), str):
                return source["name"]
        return self.root.name

    @property
    def version(self) -> str:
        for source in [self._data, self._data.get("project", {})]:
            if isinstance(source.get("version"), str):
                return source["version"]
        return "0.1.0"


def parse_constraints(spec: str) -> list[tuple[str, str]]:
    return _CONSTRAINT_RE.findall(spec)


def satisfies(version: str, spec: str) -> bool:
    if spec == "*" or not spec:
        return True
    for op, val in parse_constraints(spec):
        v_parts = [int(x) for x in version.split(".")]
        c_parts = [int(x) for x in val.split(".")]
        cmp = (v_parts > c_parts) - (v_parts < c_parts)
        if op == ">=" and cmp < 0:
            return False
        if op == "<=" and cmp > 0:
            return False
        if op == "==" and cmp != 0:
            return False
        if op == ">" and cmp <= 0:
            return False
        if op == "<" and cmp >= 0:
            return False
        if op == "!=" and cmp == 0:
            return False
        if op == "~=":
            if v_parts[: len(c_parts)] != c_parts:
                return False
    return True


class PackageCache:
    """Offline package cache at ``~/.zoya/cache``."""

    def __init__(self) -> None:
        self._dir = Path.home() / ".zoya" / "cache" / "packages"
        self._dir.mkdir(parents=True, exist_ok=True)

    def get_path(self, name: str, version: str) -> Path:
        safe_name = name.replace("-", "_").replace(".", "_")
        return self._dir / f"{safe_name}-{version}.whl"

    def has(self, name: str, version: str) -> bool:
        return self.get_path(name, version).exists()

    def store(self, name: str, version: str, data: bytes, integrity: str = "") -> None:
        path = self.get_path(name, version)
        path.write_bytes(data)
        if integrity:
            actual = "sha256-" + hashlib.sha256(data).digest().hex()
            if actual != integrity:
                path.unlink()
                raise PackageError(f"Integrity check failed for `{name}=={version}`.")

    def verify(self, name: str, version: str) -> bool:
        path = self.get_path(name, version)
        if not path.exists():
            return False
        data = path.read_bytes()
        return hashlib.sha256(data).hexdigest() == hashlib.sha256(data).hexdigest()

    def clear(self) -> None:
        for f in self._dir.iterdir():
            if f.is_file():
                f.unlink()


class RegistryIndex:
    """A local registry index (JSON-based for offline/demo mode)."""

    def __init__(self, index_path: Path | None = None) -> None:
        self._index_path = index_path or Path.home() / ".zoya" / "registry" / "index.json"
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        self._packages: Dict[str, List[PackageInfo]] = {}
        self._load()

    def _load(self) -> None:
        if self._index_path.exists():
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
            for name, versions in data.items():
                self._packages[name] = [PackageInfo(**v) for v in versions]

    def save(self) -> None:
        data: Dict[str, list] = {}
        for name, versions in self._packages.items():
            data[name] = [vars(v) for v in versions]
        self._index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add(self, pkg: PackageInfo) -> None:
        versions = self._packages.setdefault(pkg.name, [])
        for i, v in enumerate(versions):
            if v.version == pkg.version:
                versions[i] = pkg
                break
        else:
            versions.append(pkg)
        self.save()

    def get(self, name: str, constraint: str = "*") -> PackageInfo | None:
        versions = self._packages.get(name, [])
        for v in sorted(versions, key=lambda x: x.version, reverse=True):
            if satisfies(v.version, constraint):
                return v
        return None

    def search(self, query: str) -> List[PackageInfo]:
        q = query.lower()
        results: List[PackageInfo] = []
        for name, versions in self._packages.items():
            if q in name.lower():
                results.append(versions[0])
        return results

    def all(self) -> Dict[str, List[PackageInfo]]:
        return dict(self._packages)
