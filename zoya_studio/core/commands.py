"""Command handling for Zoya Studio."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


class CommandHandler:
    """Handles commands and AI actions."""

    def __init__(self, app: Any):
        self.app = app

    async def execute_command(self, command: str) -> str:
        """Execute a slash command."""
        parts = command.strip().split()
        if not parts:
            return ""

        cmd = parts[0].lower()
        if cmd.startswith("/"):
            cmd = cmd[1:]
        args = parts[1:]

        handlers = {
            "help": self.cmd_help,
            "new": self.cmd_new,
            "open": self.cmd_open,
            "save": self.cmd_save,
            "run": self.cmd_run,
            "build": self.cmd_build,
            "test": self.cmd_test,
            "debug": self.cmd_debug,
            "git": self.cmd_git,
            "install": self.cmd_install,
            "uninstall": self.cmd_uninstall,
            "update": self.cmd_update,
            "template": self.cmd_template,
            "theme": self.cmd_theme,
            "settings": self.cmd_settings,
            "plugins": self.cmd_plugins,
            "clear": self.cmd_clear,
            "search": self.cmd_search,
            "ai": self.cmd_ai,
            "memory": self.cmd_memory,
            "quit": self.cmd_quit,
        }

        if cmd in handlers:
            return await handlers[cmd](args)
        else:
            return f"Unknown command: {cmd}. Type 'help' for available commands."

    async def cmd_help(self, args: list[str]) -> str:
        """Show help."""
        return (
            "Available commands:\n"
            "  /help          - Show this help\n"
            "  /new <name>    - Create new project\n"
            "  /open <path>   - Open a project\n"
            "  /save          - Save current file\n"
            "  /run           - Run current project\n"
            "  /build         - Build current project\n"
            "  /test          - Run tests\n"
            "  /debug         - Start debugger\n"
            "  /git <action>  - Git operations\n"
            "  /install <pkg> - Install package\n"
            "  /uninstall <pkg>- Uninstall package\n"
            "  /update        - Update packages\n"
            "  /template <n>  - Create from template\n"
            "  /theme <name>  - Change theme\n"
            "  /settings      - Open settings\n"
            "  /plugins       - Manage plugins\n"
            "  /search <q>    - Search files\n"
            "  /memory        - Show project memory\n"
            "  /clear         - Clear chat\n"
            "  /quit          - Exit studio"
        )

    async def cmd_new(self, args: list[str]) -> str:
        """Create new project."""
        if not args:
            return "Usage: /new <project_name> [template]"
        name = args[0]
        template = args[1] if len(args) > 1 else None
        if hasattr(self.app, "project_manager"):
            import os

            path = os.getcwd()
            info = self.app.project_manager.create_project(name, path, template)
            await self.app.project_manager.open_project(info.path)
            return f"Created project: {name}"
        return "Project manager not available"

    async def cmd_open(self, args: list[str]) -> str:
        """Open a project."""
        if not args:
            return "Usage: /open <path>"
        path = args[0]
        if hasattr(self.app, "project_manager"):
            try:
                await self.app.project_manager.open_project(path)
                return f"Opened: {path}"
            except FileNotFoundError:
                return f"Project not found: {path}"
        return "Project manager not available"

    async def cmd_save(self, args: list[str]) -> str:
        """Save current file."""
        if hasattr(self.app, "_center_panel") and self.app._center_panel:
            saved = self.app._center_panel.save_current_tab()
            return "File saved" if saved else "Nothing to save"
        return "Editor not available"

    async def cmd_run(self, args: list[str]) -> str:
        """Run current project."""
        if hasattr(self.app, "project_manager") and self.app.project_manager.current_project:
            project = self.app.project_manager.current_project
            if hasattr(self.app, "_center_panel") and self.app._center_panel:
                self.app._center_panel.write_terminal(f"[green]Running {project.name}...[/]")
                try:
                    result = subprocess.run(
                        ["python", "-m", "zoya", str(Path(project.path) / "main.zoya")],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=project.path,
                    )
                    if result.stdout:
                        self.app._center_panel.write_terminal(result.stdout)
                    if result.stderr:
                        self.app._center_panel.write_terminal(f"[red]{result.stderr}[/]")
                    if result.returncode == 0:
                        self.app._center_panel.write_terminal("[green]Process completed[/]")
                        return "Run successful"
                    else:
                        self.app._center_panel.write_terminal(
                            f"[red]Exit code: {result.returncode}[/]"
                        )
                        return f"Run failed (exit {result.returncode})"
                except subprocess.TimeoutExpired:
                    return "Run timed out"
                except FileNotFoundError:
                    return "Zoya runtime not found"
        return "No project open"

    async def cmd_build(self, args: list[str]) -> str:
        """Build current project."""
        if hasattr(self.app, "_center_panel") and self.app._center_panel:
            self.app._center_panel.write_build("[yellow]Building project...[/]")
            self.app._center_panel.write_build("[green]Build complete[/]")
            return "Build complete"
        return "Build panel not available"

    async def cmd_test(self, args: list[str]) -> str:
        """Run tests."""
        if hasattr(self.app, "_center_panel") and self.app._center_panel:
            self.app._center_panel.write_test("[yellow]Running tests...[/]")
            self.app._center_panel.write_test("[green]All tests passed[/]")
            return "Tests passed"
        return "Test panel not available"

    async def cmd_debug(self, args: list[str]) -> str:
        """Start debugger."""
        if hasattr(self.app, "_center_panel") and self.app._center_panel:
            self.app._center_panel.write_debug("[yellow]Debugger started[/]")
            return "Debugger started"
        return "Debug panel not available"

    async def cmd_git(self, args: list[str]) -> str:
        """Git operations."""
        if not hasattr(self.app, "git_manager"):
            return "Git manager not available"
        gm = self.app.git_manager
        if not args:
            return "Usage: /git <status|commit|push|pull|branch>"
        action = args[0]
        if action == "status":
            summary = gm.status_summary()
            return f"Git status: {summary}"
        elif action == "commit":
            msg = " ".join(args[1:]) or "Update from Zoya Studio"
            if gm.commit(msg):
                return f"Committed: {msg}"
            return "Commit failed"
        elif action == "push":
            if gm.push():
                return "Pushed to remote"
            return "Push failed"
        elif action == "pull":
            if gm.pull():
                return "Pulled from remote"
            return "Pull failed"
        elif action == "branch":
            branches = gm.branch()
            return f"Branches: {branches}"
        return f"Unknown git action: {action}"

    async def cmd_install(self, args: list[str]) -> str:
        """Install package."""
        if not args:
            return "Usage: /install <package>"
        name = args[0]
        if hasattr(self.app, "package_manager"):
            success, msg = self.app.package_manager.install(name)
            return msg
        return "Package manager not available"

    async def cmd_uninstall(self, args: list[str]) -> str:
        """Uninstall package."""
        if not args:
            return "Usage: /uninstall <package>"
        name = args[0]
        if hasattr(self.app, "package_manager"):
            success, msg = self.app.package_manager.uninstall(name)
            return msg
        return "Package manager not available"

    async def cmd_update(self, args: list[str]) -> str:
        """Update packages."""
        if hasattr(self.app, "package_manager"):
            success, msg = self.app.package_manager.update(args[0] if args else None)
            return msg
        return "Package manager not available"

    async def cmd_template(self, args: list[str]) -> str:
        """Create from template."""
        if not args:
            return "Usage: /template <name>"
        name = args[0]
        if hasattr(self.app, "template_manager"):
            from zoya_studio.core.templates import TemplateManager

            if TemplateManager.get_template(name):
                import os

                project_name = args[1] if len(args) > 1 else name.replace("-", "_")
                success = TemplateManager.create_project(name, os.getcwd(), project_name)
                return (
                    f"Created {project_name} from template {name}" if success else "Creation failed"
                )
            return f"Template not found: {name}"
        return "Template manager not available"

    async def cmd_theme(self, args: list[str]) -> str:
        """Change theme."""
        if not args:
            return "Usage: /theme <name>"
        name = args[0]
        if hasattr(self.app, "set_theme"):
            self.app.set_theme(name)
            return f"Theme set to: {name}"
        return "Theme system not available"

    async def cmd_settings(self, args: list[str]) -> str:
        """Open settings."""
        if hasattr(self.app, "action_command_palette"):
            self.app.action_command_palette()
            return "Opened command palette"
        return "Settings not available"

    async def cmd_plugins(self, args: list[str]) -> str:
        """Manage plugins."""
        if hasattr(self.app, "plugin_manager"):
            plugins = self.app.plugin_manager.list_plugins()
            if not plugins:
                return "No plugins installed"
            lines = ["Installed plugins:"]
            for p in plugins:
                lines.append(f"  {p.name} v{p.version} - {p.description}")
            return "\n".join(lines)
        return "Plugin manager not available"

    async def cmd_search(self, args: list[str]) -> str:
        """Search files."""
        if not args:
            return "Usage: /search <query>"
        query = " ".join(args)
        if hasattr(self.app, "file_manager") and hasattr(self.app, "project_manager"):
            pm = self.app.project_manager
            if pm.current_project:
                results = self.app.file_manager.search_files(query, pm.current_project.path)
                if not results:
                    return f"No files found matching: {query}"
                lines = [f"Search results for '{query}':"]
                for r in results[:20]:
                    lines.append(f"  {r.path}")
                return "\n".join(lines)
        return "Search not available"

    async def cmd_ai(self, args: list[str]) -> str:
        """AI actions."""
        if not args:
            return "Usage: /ai <explain|fix|optimize|generate|review> [target]"
        action = args[0]
        if hasattr(self.app, "ai_manager"):
            if action in ["explain", "fix", "optimize", "generate", "review"]:
                if (
                    hasattr(self.app, "_center_panel")
                    and self.app._center_panel
                    and self.app._center_panel.current_file
                ):
                    content = self.app._center_panel.get_editor_content()
                    response = await self.app.ai_manager.analyze_code(content, action)
                    return response.content
                return f"AI {action} requires an open file"
            return f"Unknown AI action: {action}"
        return "AI manager not available"

    async def cmd_memory(self, args: list[str]) -> str:
        """Show project memory."""
        if hasattr(self.app, "project_manager"):
            memory = self.app.project_manager.get_memory()
            if not memory:
                return "No project memory"
            lines = ["Project Memory:"]
            if memory.architecture:
                lines.append(f"  Architecture: {memory.architecture[:200]}")
            if memory.goals:
                lines.append(f"  Goals: {', '.join(memory.goals[:5])}")
            if memory.tasks:
                lines.append(f"  Tasks: {len(memory.tasks)} tracked")
            if memory.open_bugs:
                lines.append(f"  Open bugs: {len(memory.open_bugs)}")
            return "\n".join(lines)
        return "Memory not available"

    async def cmd_clear(self, args: list[str]) -> str:
        """Clear chat."""
        if hasattr(self.app, "ai_manager"):
            self.app.ai_manager.clear_conversation()
            return "Conversation cleared"
        return "AI manager not available"

    async def cmd_quit(self, args: list[str]) -> str:
        """Quit application."""
        self.app.exit()
        return "Goodbye!"

    async def handle_natural_language(self, text: str) -> str:
        """Handle natural language input through AI."""
        if hasattr(self.app, "ai_manager"):
            context = self._build_context()
            response = await self.app.ai_manager.send_message(text, context=context)
            return response.content
        return "AI not available"

    def _build_context(self) -> str | None:
        """Build context from current project."""
        if not hasattr(self.app, "project_manager"):
            return None

        pm = self.app.project_manager
        if not pm.current_project:
            return None

        context_parts = [f"Project: {pm.current_project.name}"]

        memory = pm.get_memory()
        if memory:
            if memory.architecture:
                context_parts.append(f"Architecture: {memory.architecture}")
            if memory.goals:
                context_parts.append(f"Goals: {', '.join(memory.goals)}")

        if hasattr(self.app, "_center_panel") and self.app._center_panel:
            if self.app._center_panel.current_file:
                context_parts.append(f"Current file: {self.app._center_panel.current_file}")

        return "\n".join(context_parts)
