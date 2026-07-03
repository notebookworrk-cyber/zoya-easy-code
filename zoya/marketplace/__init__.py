__version__ = "0.1.0"

import re
import time
from typing import Any, Dict, List, Optional, Tuple


__all__ = [
    "PackageInfo",
    "PackageVersion",
    "MarketplaceRegistry",
    "PackageError",
    "DependencyResolver",
]


class PackageError(Exception):
    pass


class PackageInfo:
    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        author: str,
        license: str = "MIT",
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        downloads: int = 0,
        rating: float = 0.0,
        created_at: Optional[float] = None,
        updated_at: Optional[float] = None,
        homepage: Optional[str] = None,
        repository: Optional[str] = None,
        readme: Optional[str] = None,
    ) -> None:
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.license = license
        self.dependencies = dependencies or []
        self.tags = tags or []
        self.downloads = downloads
        self.rating = rating
        now = time.time()
        self.created_at = created_at if created_at is not None else now
        self.updated_at = updated_at if updated_at is not None else now
        self.homepage = homepage
        self.repository = repository
        self.readme = readme


class PackageVersion:
    def __init__(
        self,
        package: str,
        version: str,
        files: Optional[Dict[str, str]] = None,
        manifest: Optional[Dict[str, Any]] = None,
        published_at: Optional[float] = None,
    ) -> None:
        self.package = package
        self.version = version
        self.files = files or {}
        self.manifest = manifest or {}
        self.published_at = published_at if published_at is not None else time.time()


class DependencyResolver:
    def resolve(self, name: str, version: str = "*") -> List[Tuple[str, str]]:
        return [(name, version)]

    def check_conflicts(self, dependencies: List[Tuple[str, str]]) -> List[str]:
        seen: Dict[str, str] = {}
        conflicts: List[str] = []
        for pkg, ver in dependencies:
            if pkg in seen and seen[pkg] != ver:
                conflicts.append(f"{pkg}: {seen[pkg]} vs {ver}")
            seen[pkg] = ver
        return conflicts

    def validate_version(self, version: str) -> bool:
        pattern = r"^\d+\.\d+\.\d+$"
        return bool(re.match(pattern, version))

    def compare_versions(self, v1: str, v2: str) -> int:
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]
        max_len = max(len(parts1), len(parts2))
        parts1.extend([0] * (max_len - len(parts1)))
        parts2.extend([0] * (max_len - len(parts2)))
        for a, b in zip(parts1, parts2):
            if a < b:
                return -1
            if a > b:
                return 1
        return 0

    def satisfies(self, version: str, constraint: str) -> bool:
        constraint = constraint.strip()
        if constraint == "*":
            return True
        if constraint.startswith("^"):
            base = constraint[1:]
            parts = base.split(".")
            major = parts[0]
            return version.startswith(major + ".")
        if constraint.startswith(">="):
            return self.compare_versions(version, constraint[2:]) >= 0
        if constraint.startswith("<="):
            return self.compare_versions(version, constraint[2:]) <= 0
        if constraint.startswith(">"):
            return self.compare_versions(version, constraint[1:]) > 0
        if constraint.startswith("<"):
            return self.compare_versions(version, constraint[1:]) < 0
        if constraint.startswith("="):
            return self.compare_versions(version, constraint[1:]) == 0
        if constraint.startswith("~>"):
            base = constraint[2:]
            parts = base.split(".")
            if len(parts) == 2:
                return version.startswith(parts[0] + "." + parts[1])
            return version.startswith(parts[0] + ".")
        return self.compare_versions(version, constraint) == 0


class MarketplaceRegistry:
    def __init__(self) -> None:
        self._packages: Dict[str, PackageInfo] = {}
        self._versions: Dict[str, Dict[str, PackageVersion]] = {}
        self._deprecated: Dict[str, str] = {}

    def register(self, package: PackageInfo) -> str:
        if package.name in self._packages:
            raise PackageError(f"Package '{package.name}' already registered")
        self._packages[package.name] = package
        self._versions[package.name] = {}
        return package.name

    def publish_version(self, package_name: str, version: PackageVersion) -> None:
        if package_name not in self._packages:
            raise PackageError(f"Package '{package_name}' not registered")
        self._versions[package_name][version.version] = version
        pkg = self._packages[package_name]
        pkg.version = version.version
        pkg.updated_at = time.time()

    def get_package(self, name: str) -> Optional[PackageInfo]:
        return self._packages.get(name)

    def get_version(self, name: str, version: str) -> Optional[PackageVersion]:
        versions = self._versions.get(name)
        if versions is None:
            return None
        return versions.get(version)

    def search(self, query: str, tags: Optional[List[str]] = None) -> List[PackageInfo]:
        query_lower = query.lower()
        results: List[PackageInfo] = []
        for pkg in self._packages.values():
            if query_lower in pkg.name.lower() or query_lower in pkg.description.lower():
                if tags is None or any(t in pkg.tags for t in tags):
                    results.append(pkg)
        return results

    def list_by_tag(self, tag: str) -> List[PackageInfo]:
        return [pkg for pkg in self._packages.values() if tag in pkg.tags]

    def list_popular(self, limit: int = 10) -> List[PackageInfo]:
        sorted_pkgs = sorted(
            self._packages.values(), key=lambda p: p.downloads, reverse=True
        )
        return sorted_pkgs[:limit]

    def list_recent(self, limit: int = 10) -> List[PackageInfo]:
        sorted_pkgs = sorted(
            self._packages.values(), key=lambda p: p.created_at, reverse=True
        )
        return sorted_pkgs[:limit]

    def install(self, name: str, version: str = "latest") -> Dict[str, str]:
        if name not in self._packages:
            raise PackageError(f"Package '{name}' not found")
        if name in self._deprecated:
            raise PackageError(f"Package '{name}' is deprecated: {self._deprecated[name]}")
        versions = self._versions.get(name, {})
        if not versions:
            raise PackageError(f"No versions published for '{name}'")
        if version == "latest":
            selected = max(versions.keys(), key=lambda v: [int(x) for x in v.split(".")])
        elif version in versions:
            selected = version
        else:
            raise PackageError(f"Version '{version}' not found for '{name}'")
        self._packages[name].downloads += 1
        return dict(versions[selected].files)

    def uninstall(self, name: str) -> None:
        if name not in self._packages:
            raise PackageError(f"Package '{name}' not found")
        del self._packages[name]
        self._versions.pop(name, None)
        self._deprecated.pop(name, None)

    def update(self, name: str) -> Optional[str]:
        if name not in self._packages:
            raise PackageError(f"Package '{name}' not found")
        versions = self._versions.get(name, {})
        if not versions:
            return None
        current = self._packages[name].version
        latest = max(versions.keys(), key=lambda v: [int(x) for x in v.split(".")])
        resolver = DependencyResolver()
        if resolver.compare_versions(latest, current) > 0:
            self._packages[name].version = latest
            self._packages[name].updated_at = time.time()
            return latest
        return None

    def deprecate(self, name: str, reason: str = "") -> None:
        if name not in self._packages:
            raise PackageError(f"Package '{name}' not found")
        self._deprecated[name] = reason

    def get_dependency_tree(self, name: str) -> Dict[str, Any]:
        pkg = self._packages.get(name)
        if pkg is None:
            return {}
        tree: Dict[str, Any] = {
            "name": pkg.name,
            "version": pkg.version,
            "dependencies": [],
        }
        for dep in pkg.dependencies:
            dep_name = dep.split(">")[0].split("<")[0].split("=")[0].split("@")[0].strip()
            tree["dependencies"].append(self.get_dependency_tree(dep_name))
        return tree

    def check_updates(self) -> List[Tuple[str, str, str]]:
        resolver = DependencyResolver()
        updates: List[Tuple[str, str, str]] = []
        for name, pkg in self._packages.items():
            versions = self._versions.get(name, {})
            if versions:
                latest = max(versions.keys(), key=lambda v: [int(x) for x in v.split(".")])
                if resolver.compare_versions(latest, pkg.version) > 0:
                    updates.append((name, pkg.version, latest))
        return updates

    def count(self) -> int:
        return len(self._packages)

    def clear(self) -> None:
        self._packages.clear()
        self._versions.clear()
        self._deprecated.clear()
