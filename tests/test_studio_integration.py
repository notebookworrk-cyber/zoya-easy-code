"""Integration tests for Zoya Studio end-to-end flows."""

import asyncio
import tempfile
from pathlib import Path

from zoya_studio.core.config import Config
from zoya_studio.core.project_manager import ProjectManager, ProjectMemory
from zoya_studio.core.ai_manager import AIManager
from zoya_studio.core.file_manager import FileManager
from zoya_studio.core.templates import TemplateManager
from zoya_studio.core.commands import CommandHandler
from zoya_studio.core.git_manager import GitManager
from zoya_studio.security.crypto import CryptoManager, CredentialStore


class FakeApp:
    """Minimal app for integration testing."""

    def __init__(self):
        self.config = Config()
        self.config.ai.provider = "mock"
        self.crypto = CryptoManager()
        self.ai_manager = AIManager(self)
        self.project_manager = ProjectManager(self)
        self.file_manager = FileManager(self)
        self.package_manager = None
        self.template_manager = TemplateManager
        self.git_manager = GitManager(self)
        self.plugin_manager = None
        self._center_panel = None
        self._log_messages: list[str] = []

    def exit(self):
        self.exited = True

    def log(self, message: str):
        self._log_messages.append(message)


def test_full_project_lifecycle():
    """Test creating a project, adding memory, and AI interaction."""
    app = FakeApp()
    handler = CommandHandler(app)

    with tempfile.TemporaryDirectory() as tmp:
        import os

        old_cwd = os.getcwd()
        os.chdir(tmp)
        try:
            # Create project
            result = asyncio.run(handler.execute_command("/new myproject"))
            assert "Created" in result
        finally:
            os.chdir(old_cwd)

        # Open project
        project_dir = Path(tmp) / "myproject"
        asyncio.run(app.project_manager.open_project(str(project_dir)))

        # Verify memory loaded
        memory = app.project_manager.get_memory()
        assert isinstance(memory, ProjectMemory)

        # Add a task via memory
        app.project_manager.add_task("Implement feature X", priority="high")
        assert len(memory.tasks) == 1

        # AI interaction
        asyncio.run(app.ai_manager.initialize())
        response = asyncio.run(app.ai_manager.send_message("Hello AI"))
        assert response.content
        assert len(app.ai_manager.get_conversation()) >= 2

        # Template creation in project
        success = TemplateManager.create_project("console-app", str(project_dir), "subapp")
        assert success
        assert (project_dir / "subapp" / "main.zoya").exists()


def test_credential_encryption_flow():
    """Test API key encryption and retrieval."""
    with tempfile.TemporaryDirectory() as tmp:
        crypto = CryptoManager(str(Path(tmp) / "key.bin"))
        store = CredentialStore(crypto)

        # Store API key
        store.store("openai_key", "sk-secret-12345")
        assert store.retrieve("openai_key") == "sk-secret-12345"

        # Config stores encrypted
        config = Config()
        config.ai.provider = "openai"
        encrypted = crypto.encrypt("sk-secret-12345")
        config.ai.api_key = encrypted
        decrypted = crypto.decrypt(config.ai.api_key)
        assert decrypted == "sk-secret-12345"


def test_settings_persistence():
    """Test config save/load round trip with theme."""
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        config = Config()
        config.theme.name = "dracula"
        config.ai.provider = "anthropic"
        config.editor.tab_size = 2
        config.save(str(config_path))

        loaded = Config.load(str(config_path))
        assert loaded.theme.name == "dracula"
        assert loaded.ai.provider == "anthropic"
        assert loaded.editor.tab_size == 2


def test_multi_manager_coordination():
    """Test managers work together."""
    app = FakeApp()

    with tempfile.TemporaryDirectory() as tmp:
        # Create project
        info = app.project_manager.create_project("coord", tmp)
        asyncio.run(app.project_manager.open_project(info.path))

        # File manager set to project dir
        app.file_manager.set_directory(info.path)

        # Write a file
        test_file = Path(info.path) / "test.zoya"
        app.file_manager.write_file(str(test_file), "print 'hello'")

        # Search for it
        results = app.file_manager.search_files("test", info.path)
        assert any(r.name == "test.zoya" for r in results)

        # AI context includes project
        handler = CommandHandler(app)
        context = handler._build_context()
        assert context is not None
        assert "coord" in context
