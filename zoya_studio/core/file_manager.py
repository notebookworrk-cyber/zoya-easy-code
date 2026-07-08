"""File management for Zoya Studio."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from zoya_studio.core.config import Config


@dataclass
class FileInfo:
    """File information."""
    name: str
    path: str
    is_dir: bool
    size: int = 0
    modified: float = 0.0
    extension: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "is_dir": self.is_dir,
            "size": self.size,
            "modified": self.modified,
            "extension": self.extension,
        }


class FileManager:
    """Manages file operations."""

    EXCLUDE_DIRS = {
        ".git", "__pycache__", ".zoya", "node_modules",
        ".venv", "venv", ".idea", ".vscode", "dist", "build",
        ".pytest_cache", ".ruff_cache", ".mypy_cache",
    }

    EXCLUDE_FILES = {
        ".DS_Store", "Thumbs.db", "*.pyc", "*.pyo", "*.tmp", "*.swp",
    }

    def __init__(self, app: Any):
        self.app = app
        self.config = app.config if hasattr(app, "config") else Config.load()
        self.current_dir: Path | None = None
        self.recent_files: list[str] = []
        self._clipboard: FileInfo | None = None
        self._clipboard_cut = False

    def set_directory(self, path: str) -> None:
        """Set current directory."""
        self.current_dir = Path(path)

    def list_directory(self, path: str | None = None) -> list[FileInfo]:
        """List directory contents."""
        target = Path(path) if path else self.current_dir
        if not target or not target.exists():
            return []

        items: list[FileInfo] = []
        try:
            for entry in target.iterdir():
                if entry.name in self.EXCLUDE_DIRS:
                    continue
                if any(entry.match(p) for p in self.EXCLUDE_FILES):
                    continue

                try:
                    stat = entry.stat()
                    info = FileInfo(
                        name=entry.name,
                        path=str(entry),
                        is_dir=entry.is_dir(),
                        size=stat.st_size if entry.is_file() else 0,
                        modified=stat.st_mtime,
                        extension=entry.suffix if entry.is_file() else "",
                    )
                    items.append(info)
                except (OSError, PermissionError):
                    continue

            items.sort(key=lambda x: (not x.is_dir, x.name.lower()))
            return items
        except PermissionError:
            return []

    def read_file(self, path: str) -> str | None:
        """Read file content."""
        p = Path(path)
        if not p.exists() or not p.is_file():
            return None

        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            try:
                return p.read_text(encoding="latin-1", errors="replace")
            except Exception:
                return None

    def write_file(self, path: str, content: str) -> bool:
        """Write file content."""
        p = Path(path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            self.add_recent(str(p))
            return True
        except (OSError, PermissionError):
            return False

    def create_file(self, path: str, content: str = "") -> bool:
        """Create a new file."""
        p = Path(path)
        if p.exists():
            return False
        return self.write_file(path, content)

    def create_directory(self, path: str) -> bool:
        """Create a new directory."""
        p = Path(path)
        try:
            p.mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, PermissionError):
            return False

    def delete(self, path: str, recursive: bool = False) -> bool:
        """Delete a file or directory."""
        p = Path(path)
        if not p.exists():
            return False

        try:
            if p.is_dir():
                if recursive:
                    shutil.rmtree(p)
                else:
                    p.rmdir()
            else:
                p.unlink()
            return True
        except (OSError, PermissionError):
            return False

    def rename(self, old_path: str, new_name: str) -> bool:
        """Rename a file or directory."""
        old = Path(old_path)
        new = old.parent / new_name
        if new.exists():
            return False
        try:
            old.rename(new)
            return True
        except (OSError, PermissionError):
            return False

    def copy(self, src: str, dest: str) -> bool:
        """Copy a file or directory."""
        source = Path(src)
        dest_path = Path(dest)
        if not source.exists():
            return False

        try:
            if source.is_dir():
                shutil.copytree(source, dest_path, dirs_exist_ok=True)
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest_path)
            return True
        except (OSError, PermissionError):
            return False

    def move(self, src: str, dest: str) -> bool:
        """Move a file or directory."""
        source = Path(src)
        dest_path = Path(dest)
        if not source.exists() or dest_path.exists():
            return False

        try:
            shutil.move(str(source), str(dest_path))
            return True
        except (OSError, PermissionError):
            return False

    def copy_to_clipboard(self, path: str) -> None:
        """Copy file to clipboard."""
        p = Path(path)
        self._clipboard = FileInfo(
            name=p.name,
            path=str(p),
            is_dir=p.is_dir(),
            size=p.stat().st_size if p.is_file() else 0,
        )
        self._clipboard_cut = False

    def cut_to_clipboard(self, path: str) -> None:
        """Cut file to clipboard."""
        p = Path(path)
        self._clipboard = FileInfo(
            name=p.name,
            path=str(p),
            is_dir=p.is_dir(),
            size=p.stat().st_size if p.is_file() else 0,
        )
        self._clipboard_cut = True

    def paste_from_clipboard(self, dest_dir: str) -> bool:
        """Paste from clipboard."""
        if not self._clipboard:
            return False

        dest = Path(dest_dir) / self._clipboard.name
        if self._clipboard_cut:
            result = self.move(self._clipboard.path, str(dest))
            if result:
                self._clipboard = None
        else:
            result = self.copy(self._clipboard.path, str(dest))

        return result

    def search_files(self, query: str, root: str | None = None,
                     pattern: str = "*") -> list[FileInfo]:
        """Search for files matching query."""
        root_path = Path(root) if root else self.current_dir
        if not root_path or not root_path.exists():
            return []

        results: list[FileInfo] = []
        query_lower = query.lower()

        for entry in root_path.rglob(pattern):
            if any(part in self.EXCLUDE_DIRS for part in entry.parts):
                continue
            if query_lower in entry.name.lower():
                try:
                    stat = entry.stat()
                    results.append(FileInfo(
                        name=entry.name,
                        path=str(entry),
                        is_dir=entry.is_dir(),
                        size=stat.st_size if entry.is_file() else 0,
                        modified=stat.st_mtime,
                        extension=entry.suffix if entry.is_file() else "",
                    ))
                except (OSError, PermissionError):
                    continue

        return results[:100]

    def search_content(self, query: str, root: str | None = None,
                       file_pattern: str = "*.zoya") -> list[dict[str, Any]]:
        """Search file content for query."""
        root_path = Path(root) if root else self.current_dir
        if not root_path or not root_path.exists():
            return []

        results: list[dict[str, Any]] = []
        query_lower = query.lower()

        for entry in root_path.rglob(file_pattern):
            if any(part in self.EXCLUDE_DIRS for part in entry.parts):
                continue
            if not entry.is_file():
                continue

            try:
                lines = entry.read_text(encoding="utf-8", errors="replace").split("\n")
                for i, line in enumerate(lines, 1):
                    if query_lower in line.lower():
                        results.append({
                            "file": str(entry),
                            "line": i,
                            "content": line.strip(),
                        })
                        if len(results) >= 200:
                            return results
            except (OSError, UnicodeDecodeError):
                continue

        return results

    def add_recent(self, path: str) -> None:
        """Add to recent files."""
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:50]
        self._save_recent()

    def _save_recent(self) -> None:
        """Save recent files to disk."""
        recent_file = Path.home() / ".zoya" / "studio" / "recent_files.json"
        recent_file.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(recent_file, "w", encoding="utf-8") as f:
            json.dump(self.recent_files, f)

    def load_recent(self) -> None:
        """Load recent files from disk."""
        recent_file = Path.home() / ".zoya" / "studio" / "recent_files.json"
        if recent_file.exists():
            try:
                import json
                with open(recent_file, "r", encoding="utf-8") as f:
                    self.recent_files = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.recent_files = []

    def get_file_preview(self, path: str, lines: int = 20) -> str:
        """Get file preview."""
        content = self.read_file(path)
        if content is None:
            return ""
        preview_lines = content.split("\n")[:lines]
        return "\n".join(preview_lines)

    def get_language(self, path: str) -> str:
        """Detect language from extension."""
        ext = Path(path).suffix.lower()
        lang_map = {
            ".zoya": "zoya",
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".jsx": "jsx",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".md": "markdown",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
            ".sh": "bash",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
        }
        return lang_map.get(ext, "text")

    def is_text_file(self, path: str) -> bool:
        """Check if file is a text file."""
        text_extensions = {
            ".zoya", ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml",
            ".yml", ".toml", ".md", ".html", ".css", ".sql", ".sh", ".c",
            ".cpp", ".h", ".rs", ".go", ".java", ".txt", ".cfg", ".ini",
            ".env", ".log", ".xml", ".csv",
        }
        return Path(path).suffix.lower() in text_extensions

    def format_size(self, size: int) -> str:
        """Format file size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def format_time(self, mtime: float) -> str:
        """Format modification time."""
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime("%Y-%m-%d %H:%M")

    def get_tree(self, root: str | None = None) -> str:
        """Get directory tree as string."""
        root_path = Path(root) if root else self.current_dir
        if not root_path or not root_path.exists():
            return ""

        lines: list[str] = []
        self._tree_recursive(root_path, "", lines, 0)
        return "\n".join(lines)

    def _tree_recursive(self, path: Path, prefix: str, lines: list[str], depth: int) -> None:
        """Recursively build tree."""
        if depth > 10:
            return

        items = self.list_directory(str(path))
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{item.name}")

            if item.is_dir:
                extension = "    " if is_last else "│   "
                self._tree_recursive(Path(item.path), prefix + extension, lines, depth + 1)
