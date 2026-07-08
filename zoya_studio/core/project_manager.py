"""Project management for Zoya Studio."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from zoya_studio.core.config import Config


@dataclass
class ProjectInfo:
    """Project information."""
    name: str
    path: str
    created: str = ""
    last_opened: str = ""
    favorite: bool = False
    git_repo: bool = False
    description: str = ""
    language: str = "zoya"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectInfo":
        return cls(**data)


@dataclass
class ProjectMemory:
    """Project memory structure."""
    architecture: str = ""
    coding_style: str = ""
    goals: list[str] = field(default_factory=list)
    tasks: list[dict[str, Any]] = field(default_factory=list)
    completed_work: list[str] = field(default_factory=list)
    open_bugs: list[str] = field(default_factory=list)
    important_files: list[str] = field(default_factory=list)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    conversations: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectMemory":
        return cls(**data)


class ProjectManager:
    """Manages projects and project memory."""

    def __init__(self, app: Any):
        self.app = app
        self.config = app.config if hasattr(app, "config") else Config.load()
        self.current_project: ProjectInfo | None = None
        self.recent_projects: list[ProjectInfo] = []
        self.favorites: list[ProjectInfo] = []
        self.examples: list[ProjectInfo] = []
        self.templates: list[ProjectInfo] = []
        self._memory: ProjectMemory | None = None
        self._memory_cache: dict[str, ProjectMemory] = {}

        self._projects_file = Path.home() / ".zoya" / "studio" / "projects.json"
        self._examples_dir = Path.home() / ".zoya" / "studio" / "examples"
        self._templates_dir = Path.home() / ".zoya" / "studio" / "templates"

        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensure directories exist."""
        for d in [self._projects_file.parent, self._examples_dir, self._templates_dir]:
            d.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """Initialize project manager."""
        self.load_projects()
        self.discover_examples()
        self.discover_templates()

    def load_projects(self) -> None:
        """Load recent and favorite projects from disk."""
        if self._projects_file.exists():
            try:
                with open(self._projects_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.recent_projects = [
                    ProjectInfo.from_dict(p) for p in data.get("recent", [])
                ]
                self.favorites = [
                    ProjectInfo.from_dict(p)
                    for p in data.get("favorites", [])
                    if p.get("favorite", False)
                ]
            except (json.JSONDecodeError, KeyError):
                self.recent_projects = []
                self.favorites = []

    def save_projects(self) -> None:
        """Save project list to disk."""
        data = {
            "recent": [p.to_dict() for p in self.recent_projects[:50]],
            "favorites": [p.to_dict() for p in self.favorites],
        }
        with open(self._projects_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def discover_examples(self) -> None:
        """Discover example projects."""
        self.examples = []
        if self._examples_dir.exists():
            for path in self._examples_dir.iterdir():
                if path.is_dir() and (path / "zoya.toml").exists():
                    info = ProjectInfo(
                        name=path.name,
                        path=str(path),
                        description="Example project",
                        tags=["example"],
                    )
                    self.examples.append(info)

    def discover_templates(self) -> None:
        """Discover template projects."""
        self.templates = []
        if self._templates_dir.exists():
            for path in self._templates_dir.iterdir():
                if path.is_dir():
                    info = ProjectInfo(
                        name=path.name,
                        path=str(path),
                        description="Template project",
                        tags=["template"],
                    )
                    self.templates.append(info)

    async def open_project(self, path: str) -> ProjectInfo:
        """Open a project."""
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Project not found: {path}")

        if path_obj.is_file():
            path_obj = path_obj.parent

        name = path_obj.name
        info = ProjectInfo(
            name=name,
            path=str(path_obj),
            last_opened=datetime.now().isoformat(),
            git_repo=self._is_git_repo(path_obj),
        )

        existing = next(
            (p for p in self.recent_projects if p.path == str(path_obj)), None
        )
        if existing:
            existing.last_opened = info.last_opened
            existing.git_repo = info.git_repo
            self.recent_projects.remove(existing)
            self.recent_projects.insert(0, existing)
            self.current_project = existing
        else:
            self.recent_projects.insert(0, info)
            self.current_project = info

        self.recent_projects = self.recent_projects[:50]
        self.save_projects()

        await self._load_memory()

        return self.current_project

    def _is_git_repo(self, path: Path) -> bool:
        """Check if directory is a git repo."""
        return (path / ".git").exists()

    async def _load_memory(self) -> None:
        """Load project memory."""
        if not self.current_project:
            return

        if self.current_project.path in self._memory_cache:
            self._memory = self._memory_cache[self.current_project.path]
            return

        memory_file = Path(self.current_project.path) / ".zoya" / "memory.json"
        if memory_file.exists():
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._memory = ProjectMemory.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                self._memory = ProjectMemory()
        else:
            self._memory = ProjectMemory()

        self._memory_cache[self.current_project.path] = self._memory

    def save_memory(self) -> None:
        """Save current project memory."""
        if not self.current_project or not self._memory:
            return

        memory_dir = Path(self.current_project.path) / ".zoya"
        memory_dir.mkdir(parents=True, exist_ok=True)
        memory_file = memory_dir / "memory.json"

        self._memory.updated = datetime.now().isoformat()
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(self._memory.to_dict(), f, indent=2, ensure_ascii=False)

    def get_memory(self) -> ProjectMemory | None:
        """Get current project memory."""
        return self._memory

    def update_memory(self, **kwargs: Any) -> None:
        """Update memory fields."""
        if not self._memory:
            return

        for key, value in kwargs.items():
            if hasattr(self._memory, key):
                setattr(self._memory, key, value)

        self.save_memory()

    def add_conversation(self, role: str, content: str) -> None:
        """Add a conversation entry to memory."""
        if not self._memory:
            return
        self._memory.conversations.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self._memory.conversations) > self.config.memory.max_entries:
            self._memory.conversations = self._memory.conversations[
                -self.config.memory.max_entries:
            ]
        self.save_memory()

    def add_task(self, title: str, status: str = "pending",
                 priority: str = "medium") -> None:
        """Add a task to memory."""
        if not self._memory:
            return
        self._memory.tasks.append({
            "title": title,
            "status": status,
            "priority": priority,
            "created": datetime.now().isoformat(),
        })
        self.save_memory()

    def complete_task(self, title: str) -> None:
        """Mark a task as completed."""
        if not self._memory:
            return
        for task in self._memory.tasks:
            if task.get("title") == title:
                task["status"] = "completed"
                task["completed"] = datetime.now().isoformat()
        self.save_memory()

    def add_bug(self, description: str) -> None:
        """Add an open bug."""
        if not self._memory:
            return
        self._memory.open_bugs.append(description)
        self.save_memory()

    def resolve_bug(self, description: str) -> None:
        """Resolve an open bug."""
        if not self._memory:
            return
        if description in self._memory.open_bugs:
            self._memory.open_bugs.remove(description)
            self._memory.completed_work.append(f"Fixed: {description}")
        self.save_memory()

    def add_note(self, note: str) -> None:
        """Add a note to memory."""
        if not self._memory:
            return
        self._memory.notes.append(note)
        self.save_memory()

    def mark_favorite(self, project: ProjectInfo) -> None:
        """Mark a project as favorite."""
        project.favorite = True
        if project not in self.favorites:
            self.favorites.append(project)
        self.save_projects()

    def unmark_favorite(self, project: ProjectInfo) -> None:
        """Unmark a project as favorite."""
        project.favorite = False
        self.favorites = [p for p in self.favorites if p.path != project.path]
        self.save_projects()

    def remove_recent(self, project: ProjectInfo) -> None:
        """Remove from recent projects."""
        self.recent_projects = [
            p for p in self.recent_projects if p.path != project.path
        ]
        self.save_projects()

    def create_project(self, name: str, path: str,
                       template: str | None = None) -> ProjectInfo:
        """Create a new project."""
        project_path = Path(path) / name
        project_path.mkdir(parents=True, exist_ok=True)

        if template:
            template_path = self._templates_dir / template
            if template_path.exists():
                shutil.copytree(template_path, project_path, dirs_exist_ok=True)

        (project_path / "zoya.toml").write_text(
            f'[project]\nname = "{name}"\nversion = "0.1.0"\n'
            f'description = ""\nlanguage = "zoya"\n'
        )

        (project_path / "main.zoya").write_text(
            f'print "Hello from {name}!"\n'
        )

        info = ProjectInfo(
            name=name,
            path=str(project_path),
            created=datetime.now().isoformat(),
            description=f"New {template or 'blank'} project",
        )
        self.recent_projects.insert(0, info)
        self.save_projects()

        return info

    def delete_project(self, project: ProjectInfo) -> None:
        """Delete a project."""
        path_obj = Path(project.path)
        if path_obj.exists():
            shutil.rmtree(path_obj, ignore_errors=True)

        self.remove_recent(project)
        self.unmark_favorite(project)

    def rename_project(self, project: ProjectInfo, new_name: str) -> None:
        """Rename a project."""
        old_path = Path(project.path)
        new_path = old_path.parent / new_name

        if old_path.exists() and not new_path.exists():
            old_path.rename(new_path)
            project.name = new_name
            project.path = str(new_path)
            self.save_projects()

    def import_project(self, archive_path: str, dest_dir: str) -> ProjectInfo | None:
        """Import a project from archive."""
        archive = Path(archive_path)
        if not archive.exists():
            return None

        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)

        if archive.suffix == ".zip":
            shutil.unpack_archive(str(archive), str(dest))
        else:
            return None

        for item in dest.iterdir():
            if item.is_dir():
                return ProjectInfo(
                    name=item.name,
                    path=str(item),
                    description="Imported project",
                )

        return None

    def export_project(self, project: ProjectInfo, archive_path: str) -> bool:
        """Export a project to archive."""
        project_path = Path(project.path)
        if not project_path.exists():
            return False

        archive = Path(archive_path)
        archive.parent.mkdir(parents=True, exist_ok=True)

        shutil.make_archive(str(archive.with_suffix("")), "zip", str(project_path))
        return True

    def get_project_files(self, project: ProjectInfo | None = None) -> list[str]:
        """Get all files in a project."""
        if project is None:
            project = self.current_project
        if not project:
            return []

        files = []
        path_obj = Path(project.path)
        exclude = {".git", "__pycache__", ".zoya", "node_modules", ".venv", "venv"}

        for item in path_obj.rglob("*"):
            if any(part in exclude for part in item.parts):
                continue
            if item.is_file():
                files.append(str(item.relative_to(path_obj)))

        return sorted(files)

    def get_git_status_summary(self, project: ProjectInfo | None = None) -> dict[str, int]:
        """Get git status summary."""
        if project is None:
            project = self.current_project
        if not project or not project.git_repo:
            return {}

        path_obj = Path(project.path)
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(path_obj),
                capture_output=True,
                text=True,
                check=True,
            )
            lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
            status = {"modified": 0, "added": 0, "deleted": 0, "untracked": 0}
            for line in lines:
                if not line:
                    continue
                code = line[:2]
                if code[1] == "M":
                    status["modified"] += 1
                elif code[1] == "A" or code[0] == "A":
                    status["added"] += 1
                elif code[1] == "D" or code[0] == "D":
                    status["deleted"] += 1
                elif code == "??":
                    status["untracked"] += 1
            return status
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {}
