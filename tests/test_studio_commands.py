"""Tests for Zoya Studio command handler."""

import asyncio
from pathlib import Path

from zoya_studio.core.config import Config
from zoya_studio.core.commands import CommandHandler
from zoya_studio.core.ai_manager import AIManager
from zoya_studio.core.project_manager import ProjectManager
from zoya_studio.core.file_manager import FileManager
from zoya_studio.core.package_manager import PackageManager
from zoya_studio.core.templates import TemplateManager
from zoya_studio.core.git_manager import GitManager
from zoya_studio.security.crypto import CryptoManager


class FakeApp:
    def __init__(self):
        self.config = Config()
        self.config.ai.provider = "mock"
        self.crypto = CryptoManager()
        self.ai_manager = AIManager(self)
        self.project_manager = ProjectManager(self)
        self.file_manager = FileManager(self)
        self.package_manager = PackageManager(self)
        self.template_manager = TemplateManager
        self.git_manager = GitManager(self)
        self.plugin_manager = None
        self._center_panel = None

    def exit(self):
        self.exited = True


def test_command_help():
    """Test help command."""
    app = FakeApp()
    handler = CommandHandler(app)
    result = asyncio.run(handler.execute_command("/help"))
    assert "Available commands" in result
    assert "/new" in result


def test_command_new():
    """Test new project command."""
    app = FakeApp()
    handler = CommandHandler(app)
    with Path.cwd() as cwd:
        import os
        import tempfile
        tmp = tempfile.mkdtemp()
        os.chdir(tmp)
        result = asyncio.run(handler.execute_command("/new testproj"))
        assert "Created project" in result
        assert (Path(tmp) / "testproj").exists()
        os.chdir(str(cwd))


def test_command_template():
    """Test template command."""
    app = FakeApp()
    handler = CommandHandler(app)
    import os
    import tempfile
    tmp = tempfile.mkdtemp()
    cwd = os.getcwd()
    os.chdir(tmp)
    try:
        result = asyncio.run(handler.execute_command("/template console-app myapp"))
        assert "Created" in result
        assert (Path(tmp) / "myapp").exists()
    finally:
        os.chdir(cwd)


def test_command_unknown():
    """Test unknown command."""
    app = FakeApp()
    handler = CommandHandler(app)
    result = asyncio.run(handler.execute_command("/nonexistent"))
    assert "Unknown command" in result


def test_command_clear():
    """Test clear command."""
    app = FakeApp()
    handler = CommandHandler(app)
    asyncio.run(app.ai_manager.initialize())
    asyncio.run(app.ai_manager.send_message("hello"))
    result = asyncio.run(handler.execute_command("/clear"))
    assert "cleared" in result.lower()
    assert len(app.ai_manager.get_conversation()) == 1


def test_command_memory_no_project():
    """Test memory command without project."""
    app = FakeApp()
    handler = CommandHandler(app)
    result = asyncio.run(handler.execute_command("/memory"))
    assert "No project memory" in result


def test_build_context_no_project():
    """Test context building without project."""
    app = FakeApp()
    handler = CommandHandler(app)
    context = handler._build_context()
    assert context is None
