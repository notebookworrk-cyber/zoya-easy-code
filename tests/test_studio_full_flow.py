"""Full-stack integration test for Zoya Studio."""

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
from zoya_studio.plugins import PluginManager, BasePlugin


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
        self.plugin_manager = PluginManager(self)
        self._center_panel = None
        self._log_messages: list[str] = []

    def exit(self):
        self.exited = True

    def log(self, message: str):
        self._log_messages.append(message)


def test_end_to_end_developer_workflow():
    """Simulate a complete developer workflow."""
    app = FakeApp()
    handler = CommandHandler(app)

    with tempfile.TemporaryDirectory() as tmp:
        import os

        old_cwd = os.getcwd()
        os.chdir(tmp)
        try:
            # 1. Create a project from template
            result = asyncio.run(handler.execute_command("/template console-app mygame"))
            assert "Created" in result

            # 2. Open the project
            project_dir = Path(tmp) / "mygame"
            asyncio.run(app.project_manager.open_project(str(project_dir)))

            # 3. Verify memory loaded
            memory = app.project_manager.get_memory()
            assert isinstance(memory, ProjectMemory)

            # 4. Add tasks to memory
            app.project_manager.add_task("Implement game loop", priority="high")
            app.project_manager.add_task("Add sound effects", priority="medium")
            assert len(memory.tasks) == 2

            # 5. Write a source file
            app.file_manager.set_directory(str(project_dir))
            src = project_dir / "game.zoya"
            app.file_manager.write_file(
                str(src),
                "fn main():\n    print 'Game running'\nmain()\n",
            )

            # 6. Search for the file
            results = app.file_manager.search_files("game", str(project_dir))
            assert any(r.name == "game.zoya" for r in results)

            # 7. AI interaction with context
            asyncio.run(app.ai_manager.initialize())
            response = asyncio.run(app.ai_manager.send_message("Explain my game code"))
            assert response.content
            assert len(app.ai_manager.get_conversation()) >= 2

            # 8. Verify AI context includes project
            context = handler._build_context()
            assert context is not None
            assert "mygame" in context

            # 9. Complete a task
            app.project_manager.complete_task("Implement game loop")
            assert memory.tasks[0]["status"] == "completed"

            # 10. Plugin system works
            plugin_dir = Path(tmp) / "plugins" / "test-plugin"
            plugin_dir.mkdir(parents=True)
            (plugin_dir / "plugin.json").write_text(
                '{"name": "test-plugin", "version": "0.1.0", '
                '"description": "Test", "entry": "plugin.py", "permissions": []}'
            )
            (plugin_dir / "plugin.py").write_text(
                "from zoya_studio.plugins.base import BasePlugin\n\n"
                "class Plugin(BasePlugin):\n"
                "    name = 'test-plugin'\n"
                "    version = '0.1.0'\n"
                "    def activate(self):\n"
                "        self.register_command('ping', self.ping)\n"
                "    def deactivate(self):\n"
                "        self.unregister_command('ping')\n"
                "    def ping(self, *args):\n"
                "        return 'pong'\n"
            )
            app.plugin_manager.config.plugins.directory = str(Path(tmp) / "plugins")
            app.plugin_manager.config.plugins.auto_load = False
            app.plugin_manager.plugins_dir = Path(tmp) / "plugins"
            plugins = app.plugin_manager.discover_plugins()
            assert len(plugins) == 1
            assert app.plugin_manager.load_plugin(plugins[0])
            assert app.plugin_manager.execute_command("ping") == "pong"

        finally:
            os.chdir(old_cwd)


def test_security_flow():
    """Test credential encryption flow end-to-end."""
    with tempfile.TemporaryDirectory() as tmp:
        crypto = CryptoManager(str(Path(tmp) / "key.bin"))
        store = CredentialStore(crypto)

        # Store and retrieve
        store.store("openai_key", "sk-test-12345")
        assert store.retrieve("openai_key") == "sk-test-12345"

        # Config integration
        config = Config()
        config.ai.provider = "openai"
        encrypted = crypto.encrypt("sk-test-12345")
        config.ai.api_key = encrypted
        decrypted = crypto.decrypt(config.ai.api_key)
        assert decrypted == "sk-test-12345"


def test_ai_provider_switching():
    """Test switching between providers."""
    app = FakeApp()
    asyncio.run(app.ai_manager.initialize())
    assert app.ai_manager.provider.name == "mock"

    for provider in ["openai", "anthropic", "gemini", "ollama", "mock"]:
        app.ai_manager.set_provider(provider)
        assert app.ai_manager.provider.name == provider

    # Verify each provider can generate (mock or fallback)
    response = asyncio.run(app.ai_manager.send_message("test"))
    assert response.content
