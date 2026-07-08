"""Main Zoya Studio application entry point."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Static

from zoya_studio.core.config import Config, THEME_PRESETS
from zoya_studio.widgets.sidebar_left import LeftSidebar
from zoya_studio.widgets.sidebar_right import RightSidebar
from zoya_studio.widgets.center_panel import CenterPanel
from zoya_studio.widgets.bottom_bar import BottomBar
from zoya_studio.widgets.status_bar import StatusBar
from zoya_studio.core.project_manager import ProjectManager
from zoya_studio.core.ai_manager import AIManager
from zoya_studio.core.git_manager import GitManager
from zoya_studio.core.file_manager import FileManager
from zoya_studio.core.package_manager import PackageManager
from zoya_studio.core.templates import TemplateManager
from zoya_studio.core.commands import CommandHandler
from zoya_studio.plugins import PluginManager
from zoya_studio.security.crypto import CryptoManager


class CommandPaletteScreen(ModalScreen):
    """Command palette modal screen."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("enter", "execute", "Execute"),
    ]

    def __init__(self):
        super().__init__()
        self.commands = [
            ("New Project", "ctrl+n", "/new"),
            ("Open Project", "ctrl+o", "/open"),
            ("Save File", "ctrl+s", "/save"),
            ("Run Project", "f5", "/run"),
            ("Build Project", "f7", "/build"),
            ("Run Tests", "f8", "/test"),
            ("Debug", "f6", "/debug"),
            ("Git: Status", "ctrl+g", "/git status"),
            ("Git: Commit", "ctrl+shift+g", "/git commit"),
            ("Git: Push", "", "/git push"),
            ("Git: Pull", "", "/git pull"),
            ("Install Package", "", "/install"),
            ("Uninstall Package", "", "/uninstall"),
            ("Update Packages", "", "/update"),
            ("New from Template", "", "/template"),
            ("Change Theme", "ctrl+t", "/theme"),
            ("Settings", "ctrl+,", "/settings"),
            ("Plugins", "ctrl+shift+x", "/plugins"),
            ("Search Files", "ctrl+shift+f", "/search"),
            ("Project Memory", "", "/memory"),
            ("AI: Explain Code", "ctrl+alt+e", "/ai explain"),
            ("AI: Fix Errors", "ctrl+alt+f", "/ai fix"),
            ("AI: Optimize", "ctrl+alt+o", "/ai optimize"),
            ("AI: Generate Tests", "ctrl+alt+t", "/ai generate"),
            ("AI: Review", "ctrl+alt+r", "/ai review"),
            ("Clear Chat", "", "/clear"),
            ("Help", "f1", "/help"),
            ("Quit", "ctrl+q", "/quit"),
        ]

    def compose(self) -> ComposeResult:
        yield Label("⌘ Command Palette", id="palette-title")
        yield Input(placeholder="Type a command...", id="palette-input")
        yield ListView(id="palette-list")

    def on_mount(self) -> None:
        self._refresh_list("")
        self.query_one("#palette-input", Input).focus()

    def _refresh_list(self, query: str) -> None:
        list_view = self.query_one("#palette-list", ListView)
        list_view.clear()
        query_lower = query.lower()
        for name, shortcut, cmd in self.commands:
            if query_lower in name.lower() or query_lower in cmd.lower():
                list_view.append(
                    ListItem(
                        Static(f"{name:<30} {shortcut:<15} {cmd}"),
                        id=f"cmd-{cmd}",
                    )
                )

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "palette-input":
            self._refresh_list(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "palette-input":
            self._execute_selected()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.action_close()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._execute_selected()

    def _execute_selected(self) -> None:
        list_view = self.query_one("#palette-list", ListView)
        if list_view.highlighted_child:
            cmd_id = list_view.highlighted_child.id
            if cmd_id and cmd_id.startswith("cmd-"):
                command = cmd_id[4:]
                self.dismiss(command)

    def action_close(self) -> None:
        self.dismiss(None)

    def action_execute(self) -> None:
        self._execute_selected()


class QuickOpenScreen(ModalScreen):
    """Quick file open modal."""

    BINDINGS = [Binding("escape", "close", "Close")]

    def compose(self) -> ComposeResult:
        yield Label("⌘ Quick Open", id="quick-title")
        yield Input(placeholder="Search files...", id="quick-input")
        yield ListView(id="quick-list")

    def on_mount(self) -> None:
        self.query_one("#quick-input", Input).focus()
        self._refresh_list("")

    def _get_files(self, query: str) -> list:
        app = self.app
        if hasattr(app, "project_manager") and app.project_manager.current_project:
            files = app.project_manager.get_project_files()
            if query:
                query_lower = query.lower()
                files = [f for f in files if query_lower in f.lower()]
            return files[:50]
        return []

    def _refresh_list(self, query: str) -> None:
        list_view = self.query_one("#quick-list", ListView)
        list_view.clear()
        for f in self._get_files(query):
            list_view.append(ListItem(Static(f"📄 {f}"), id=f"file-{f}"))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "quick-input":
            self._refresh_list(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "quick-input":
            self._open_selected()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.action_close()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._open_selected()

    def _open_selected(self) -> None:
        list_view = self.query_one("#quick-list", ListView)
        if list_view.highlighted_child:
            item_id = list_view.highlighted_child.id
            if item_id and item_id.startswith("file-"):
                rel_path = item_id[5:]
                self.dismiss(rel_path)

    def action_close(self) -> None:
        self.dismiss(None)


class GlobalSearchScreen(ModalScreen):
    """Global search modal."""

    BINDINGS = [Binding("escape", "close", "Close")]

    def compose(self) -> ComposeResult:
        yield Label("⌕ Global Search", id="search-title")
        yield Input(placeholder="Search in files...", id="search-input")
        yield ListView(id="search-list")

    def on_mount(self) -> None:
        self.query_one("#search-input", Input).focus()

    def _search(self, query: str) -> None:
        if not query:
            return
        app = self.app
        list_view = self.query_one("#search-list", ListView)
        list_view.clear()

        if hasattr(app, "file_manager") and hasattr(app, "project_manager"):
            pm = app.project_manager
            if pm.current_project:
                results = app.file_manager.search_content(query, pm.current_project.path)
                for r in results[:50]:
                    rel = Path(r["file"]).relative_to(pm.current_project.path)
                    list_view.append(
                        ListItem(
                            Static(f"📄 {rel}:{r['line']} - {r['content'][:50]}"),
                            id=f"result-{r['file']}:{r['line']}",
                        )
                    )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            self._search(event.value)

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.action_close()

    def action_close(self) -> None:
        self.dismiss(None)


class ZoyaStudioApp(App):
    """Main Zoya Studio application."""

    TITLE = "Zoya Studio"
    SUB_TITLE = "AI-Powered Terminal IDE"
    CSS_PATH = "app.tcss"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+shift+p", "command_palette", "Command", show=True),
        Binding("ctrl+b", "toggle_left_sidebar", "Sidebar", show=True),
        Binding("ctrl+shift+b", "toggle_right_sidebar", "AI Panel", show=True),
        Binding("ctrl+`", "toggle_terminal", "Terminal", show=True),
        Binding("ctrl+p", "quick_open", "Quick Open", show=True),
        Binding("ctrl+shift+f", "global_search", "Search", show=True),
        Binding("ctrl+s", "save_file", "Save", show=True),
        Binding("ctrl+shift+s", "save_all", "Save All", show=True),
        Binding("f5", "run_project", "Run", show=True),
        Binding("f6", "debug_project", "Debug", show=True),
        Binding("ctrl+shift+t", "new_terminal", "New Terminal", show=True),
        Binding("ctrl+w", "close_tab", "Close Tab", show=True),
        Binding("ctrl+tab", "next_tab", "Next Tab", show=False),
        Binding("ctrl+shift+tab", "prev_tab", "Prev Tab", show=False),
        Binding("f1", "settings", "Settings", show=True),
        Binding("ctrl+t", "cycle_theme", "Theme", show=True),
    ]

    def __init__(self, project_path: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.project_path = project_path
        self.config = Config.load()
        self.crypto = CryptoManager()
        self.command_handler = CommandHandler(self)

        self.project_manager = ProjectManager(self)
        self.ai_manager = AIManager(self)
        self.git_manager = GitManager(self)
        self.file_manager = FileManager(self)
        self.package_manager = PackageManager(self)
        self.template_manager = TemplateManager
        self.plugin_manager = PluginManager(self)

        self._center_panel = None
        self._left_sidebar = None
        self._right_sidebar = None
        self._bottom_bar = None
        self._status_bar = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, id="header")
        yield StatusBar(id="status-bar")

        with Horizontal(id="main-container"):
            yield LeftSidebar(id="left-sidebar")
            yield CenterPanel(id="center-panel")
            yield RightSidebar(id="right-sidebar")

        yield BottomBar(id="bottom-bar")
        yield Footer(id="footer")

    async def on_mount(self) -> None:
        """Initialize the application."""
        self._center_panel = self.query_one("#center-panel", CenterPanel)
        self._left_sidebar = self.query_one("#left-sidebar", LeftSidebar)
        self._right_sidebar = self.query_one("#right-sidebar", RightSidebar)
        self._bottom_bar = self.query_one("#bottom-bar", BottomBar)
        self._status_bar = self.query_one("#status-bar", StatusBar)

        self.screen.styles.background = self.config.theme.background

        self._apply_theme()

        try:
            await self.project_manager.initialize()
            await self.ai_manager.initialize()
            await self.git_manager.initialize()
            self.file_manager.load_recent()
            self.plugin_manager.load_all()

            if self.project_path:
                await self.project_manager.open_project(self.project_path)
            else:
                self._left_sidebar.refresh_projects()

            self._update_status_bar()
            self._update_ai_provider_status()
        except Exception as e:
            self.log(f"[red]Init error: {e}[/]")

        self.call_later(self._refresh_all)

    def _apply_theme(self) -> None:
        """Apply current theme."""
        theme = self.config.theme
        self.screen.styles.background = theme.background

    def _update_status_bar(self) -> None:
        """Update status bar."""
        if self.project_manager.current_project:
            self._status_bar.set_project(self.project_manager.current_project.name)
        else:
            self._status_bar.set_project("No project")

        if self.git_manager.current_repo and self.git_manager.is_git_repo():
            branch = self.git_manager.get_current_branch()
            summary = self.git_manager.status_summary()
            has_changes = sum(summary.values()) > 0
            self._status_bar.set_git_status(branch, has_changes)
        else:
            self._status_bar.set_git_status("", False)

    def _update_ai_provider_status(self) -> None:
        """Update AI provider status."""
        provider = self.config.ai.provider
        self._status_bar.set_ai_status(provider, self.config.ai.model)

    def _refresh_all(self) -> None:
        """Refresh all panels."""
        self._left_sidebar.refresh_projects()
        self._left_sidebar.refresh_files()
        self._left_sidebar.refresh_git()
        self._right_sidebar.refresh_memory()
        self._right_sidebar.refresh_tasks()
        self._right_sidebar.refresh_docs()
        self._right_sidebar.refresh_errors()

    # Actions
    def action_quit(self) -> None:
        self.exit()

    def action_command_palette(self) -> None:
        self.push_screen(CommandPaletteScreen())

    def action_toggle_left_sidebar(self) -> None:
        self._left_sidebar.display = not self._left_sidebar.display
        self.config.ui.show_left_sidebar = self._left_sidebar.display
        self.config.save()

    def action_toggle_right_sidebar(self) -> None:
        self._right_sidebar.display = not self._right_sidebar.display
        self.config.ui.show_right_sidebar = self._right_sidebar.display
        self.config.save()

    def action_toggle_terminal(self) -> None:
        self._center_panel.toggle_terminal()

    def action_quick_open(self) -> None:
        def handle_result(result):
            if result:
                self._open_file_by_relative_path(result)

        self.push_screen(QuickOpenScreen(), handle_result)

    def action_global_search(self) -> None:
        self.push_screen(GlobalSearchScreen())

    def action_save_file(self) -> None:
        self._center_panel.save_current_tab()

    def action_save_all(self) -> None:
        saved = self._center_panel.save_all_tabs()
        self._center_panel.write_log(f"Saved {saved} files")

    def action_run_project(self) -> None:
        if self.project_manager.current_project:
            self.run_in_terminal("/run")

    def action_debug_project(self) -> None:
        if self.project_manager.current_project:
            self.run_in_terminal("/debug")

    def action_new_terminal(self) -> None:
        self._center_panel.new_terminal()

    def action_close_tab(self) -> None:
        self._center_panel.close_current_tab()

    def action_next_tab(self) -> None:
        self._center_panel.next_tab()

    def action_prev_tab(self) -> None:
        self._center_panel.prev_tab()

    def action_settings(self) -> None:
        from zoya_studio.settings import SettingsScreen

        self.push_screen(SettingsScreen(self))

    def action_cycle_theme(self) -> None:
        presets = list(THEME_PRESETS.keys())
        current = self.config.theme.name
        idx = presets.index(current) if current in presets else 0
        next_theme = presets[(idx + 1) % len(presets)]
        self.set_theme(next_theme)

    def set_theme(self, name: str) -> None:
        """Set theme by name."""
        if name in THEME_PRESETS:
            self.config.theme = THEME_PRESETS[name]
            self.config.save()
            self._apply_theme()
            self._status_bar.set_line_status(f"Theme: {name}")
            self._center_panel.write_log(f"[green]Theme changed to {name}[/]")

    def _open_file_by_relative_path(self, rel_path: str) -> None:
        """Open a file by relative path."""
        if not self.project_manager.current_project:
            return
        full_path = str(Path(self.project_manager.current_project.path) / rel_path)
        self.open_file(full_path)

    def open_file(self, path: str) -> None:
        """Open a file in the editor."""
        content = self.file_manager.read_file(path)
        if content is None:
            self._center_panel.write_log(f"[red]Cannot open: {path}[/]")
            return
        self._center_panel.open_file(path, content)
        self.file_manager.add_recent(path)

    def run_in_terminal(self, command: str) -> None:
        """Run a command."""
        asyncio.create_task(self.command_handler.execute_command(command))

    # Event handlers
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission from bottom bar."""
        if event.input.id == "command-input":
            text = event.value.strip()
            if not text:
                return

            self._bottom_bar.clear_input()

            if text.startswith("/"):
                result = await self.command_handler.execute_command(text)
                if result:
                    self._center_panel.write_log(result)
            else:
                await self._handle_ai_message(text)

    async def _handle_ai_message(self, text: str) -> None:
        """Handle AI message from bottom bar."""
        self._right_sidebar.add_message("user", text)

        if not hasattr(self.ai_manager, "provider") or not self.ai_manager.provider:
            await self.ai_manager.initialize()

        try:
            context = self.command_handler._build_context()

            async def stream_cb(chunk: str):
                self._right_sidebar.stream_message(chunk)

            response = await self.ai_manager.send_message(
                text, stream_callback=stream_cb, context=context
            )
            self._right_sidebar.add_message("assistant", response.content)
            self._update_status_bar()
        except Exception as e:
            self._right_sidebar.add_message("assistant", f"[red]Error: {e}[/]")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        btn_id = event.button.id

        handlers = {
            "send-btn": self._on_send_pressed,
            "btn-new-project": lambda: self._on_new_project(),
            "btn-open-project": lambda: self._on_open_project(),
            "btn-new-file": lambda: self._on_new_file(),
            "btn-new-folder": lambda: self._on_new_folder(),
            "btn-git-commit": lambda: self.run_in_terminal("/git commit"),
            "btn-git-push": lambda: self.run_in_terminal("/git push"),
            "btn-git-pull": lambda: self.run_in_terminal("/git pull"),
            "btn-git-branch": lambda: self.run_in_terminal("/git branch"),
            "btn-search-files": lambda: self._on_search_pressed(),
            "btn-ai-send": lambda: self._on_ai_send(),
        }

        if btn_id in handlers:
            handlers[btn_id]()

    async def _on_send_pressed(self) -> None:
        input_widget = self._bottom_bar.query_one("#command-input", Input)
        text = input_widget.value.strip()
        if text:
            input_widget.value = ""
            if text.startswith("/"):
                result = await self.command_handler.execute_command(text)
                if result:
                    self._center_panel.write_log(result)
            else:
                await self._handle_ai_message(text)

    async def _on_ai_send(self) -> None:
        input_widget = self._right_sidebar.query_one("#ai-input", Input)
        text = input_widget.value.strip()
        if text:
            input_widget.value = ""
            self._right_sidebar.add_message("user", text)
            await self._handle_ai_message(text)

    async def _on_new_project(self) -> None:
        from zoya_studio.widgets.dialogs import InputDialog

        self.push_screen(InputDialog("New Project", "Project name:"))

    async def _on_open_project(self) -> None:
        from zoya_studio.widgets.dialogs import PathDialog

        self.push_screen(PathDialog("Open Project", "Project path:"))

    async def _on_new_file(self) -> None:
        from zoya_studio.widgets.dialogs import InputDialog

        self.push_screen(InputDialog("New File", "File name:"))

    async def _on_new_folder(self) -> None:
        from zoya_studio.widgets.dialogs import InputDialog

        self.push_screen(InputDialog("New Folder", "Folder name:"))

    async def _on_search_pressed(self) -> None:
        input_widget = self._left_sidebar.query_one("#file-search-input", Input)
        query = input_widget.value.strip()
        if query and self.project_manager.current_project:
            results = self.file_manager.search_files(
                query, self.project_manager.current_project.path
            )
            list_view = self._left_sidebar.query_one("#search-results", ListView)
            list_view.clear()
            for r in results[:20]:
                list_view.append(ListItem(Static(f"📄 {r.path}"), id=f"search-{r.path}"))

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list view item selection."""
        item_id = event.item.id or ""

        if item_id.startswith("proj-") or item_id.startswith("fav-"):
            path = item_id.split("-", 1)[1]
            await self.project_manager.open_project(path)
            self._refresh_all()
            self._update_status_bar()
        elif item_id.startswith("file-"):
            path = item_id[5:]
            self.open_file(path)
        elif item_id.startswith("search-"):
            path = item_id[7:]
            self.open_file(path)

    def log(self, message: str) -> None:
        """Log a message."""
        if self._center_panel:
            self._center_panel.write_log(message)

    async def on_key(self, event: events.Key) -> None:
        """Handle global key events."""
        if event.key == "escape":
            focused = self.focused
            if hasattr(focused, "blur"):
                focused.blur()


def main(
    project: Optional[str] = typer.Argument(None, help="Project path to open"),
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Config file path"),
) -> None:
    """Zoya Studio - AI-Powered Terminal IDE for Zoya.

    Launch with: zoya studio, zoya, or python -m zoya_studio
    """
    if version:
        from zoya_studio import __version__

        print(f"Zoya Studio v{__version__}")
        return

    app = ZoyaStudioApp(project_path=project)
    app.run()


if __name__ == "__main__":
    typer.run(main)
