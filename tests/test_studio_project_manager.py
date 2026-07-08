"""Tests for Zoya Studio project manager."""

import asyncio
import tempfile
from pathlib import Path

from zoya_studio.core.config import Config
from zoya_studio.core.project_manager import ProjectManager, ProjectInfo, ProjectMemory


class FakeApp:
    def __init__(self):
        self.config = Config()


def test_project_manager_create():
    """Test creating a project."""
    app = FakeApp()
    pm = ProjectManager(app)
    with tempfile.TemporaryDirectory() as tmp:
        info = pm.create_project("testproj", tmp)
        assert info.name == "testproj"
        assert (Path(tmp) / "testproj" / "main.zoya").exists()
        assert (Path(tmp) / "testproj" / "zoya.toml").exists()


def test_project_manager_open():
    """Test opening a project."""
    app = FakeApp()
    pm = ProjectManager(app)
    with tempfile.TemporaryDirectory() as tmp:
        info = pm.create_project("testproj", tmp)
        pm2 = ProjectManager(app)
        opened = asyncio.run(pm2.open_project(info.path))
        assert opened.name == "testproj"
        assert pm2.current_project is not None
        assert pm2.get_memory() is not None


def test_project_manager_memory():
    """Test project memory operations."""
    app = FakeApp()
    pm = ProjectManager(app)
    with tempfile.TemporaryDirectory() as tmp:
        info = pm.create_project("testproj", tmp)
        asyncio.run(pm.open_project(info.path))

        pm.update_memory(architecture="Modular", goals=["Ship v1"])
        pm.add_task("Write docs", priority="high")
        pm.add_bug("Crash on exit")
        pm.add_note("Remember to test")

        memory = pm.get_memory()
        assert memory.architecture == "Modular"
        assert "Ship v1" in memory.goals
        assert len(memory.tasks) == 1
        assert len(memory.open_bugs) == 1

        pm.complete_task("Write docs")
        assert memory.tasks[0]["status"] == "completed"

        pm.resolve_bug("Crash on exit")
        assert len(memory.open_bugs) == 0


def test_project_manager_favorites():
    """Test favorite management."""
    app = FakeApp()
    pm = ProjectManager(app)
    with tempfile.TemporaryDirectory() as tmp:
        info = pm.create_project("favproj", tmp)
        pm.mark_favorite(info)
        assert info in pm.favorites
        pm.unmark_favorite(info)
        assert info not in pm.favorites


def test_project_manager_files():
    """Test getting project files."""
    app = FakeApp()
    pm = ProjectManager(app)
    with tempfile.TemporaryDirectory() as tmp:
        info = pm.create_project("fileproj", tmp)
        (Path(tmp) / "fileproj" / "extra.zoya").write_text("x")
        files = pm.get_project_files(info)
        assert "main.zoya" in files
        assert "extra.zoya" in files


def test_project_manager_delete():
    """Test deleting a project."""
    app = FakeApp()
    pm = ProjectManager(app)
    with tempfile.TemporaryDirectory() as tmp:
        info = pm.create_project("delproj", tmp)
        pm.delete_project(info)
        assert not (Path(tmp) / "delproj").exists()
