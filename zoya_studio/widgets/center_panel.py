"""Center panel widget for Zoya Studio."""

from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import Label, RichLog, TabbedContent, TabPane, TextArea


class CenterPanel(Vertical):
    """Center panel with editor, terminal, and output tabs."""

    DEFAULT_CSS = """
    CenterPanel {
        width: 1fr;
    }

    #center-tabs {
        height: 1fr;
    }

    #editor-area {
        height: 1fr;
    }

    #editor-status {
        height: 1;
        background: #0d1117;
        color: #8b949e;
        content-align: left middle;
        padding: 0 1;
    }

    #terminal-output {
        height: 1fr;
        border: solid #30363d;
    }

    #build-output {
        height: 1fr;
        border: solid #30363d;
    }

    #debug-output {
        height: 1fr;
        border: solid #30363d;
    }

    #test-output {
        height: 1fr;
        border: solid #30363d;
    }

    #log-output {
        height: 1fr;
        border: solid #30363d;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_file = None
        self.open_tabs: dict[str, str] = {}

    def compose(self):
        with TabbedContent(id="center-tabs"):
            with TabPane("Editor", id="tab-editor"):
                yield TextArea(id="editor-area", language="python")
                yield Label("Ready", id="editor-status")

            with TabPane("Terminal", id="tab-terminal"):
                yield RichLog(id="terminal-output", markup=True, highlight=True, wrap=True)

            with TabPane("Build", id="tab-build"):
                yield RichLog(id="build-output", markup=True, highlight=True, wrap=True)

            with TabPane("Debug", id="tab-debug"):
                yield RichLog(id="debug-output", markup=True, highlight=True, wrap=True)

            with TabPane("Tests", id="tab-test"):
                yield RichLog(id="test-output", markup=True, highlight=True, wrap=True)

            with TabPane("Logs", id="tab-log"):
                yield RichLog(id="log-output", markup=True, highlight=True, wrap=True)

    def on_mount(self):
        editor = self.query_one("#editor-area", TextArea)
        if hasattr(self.app, "config"):
            editor.theme = "github_dark" if self.app.config.theme.name == "dark" else "github_light"

    def open_file(self, path: str, content: str = ""):
        """Open a file in the editor."""
        editor = self.query_one("#editor-area", TextArea)
        editor.text = content
        editor.language = self._detect_language(path)
        self.current_file = path
        self.query_one("#editor-status", Label).update(f"📄 {path}")

        self.open_tabs[path] = content

    def _detect_language(self, path: str) -> str:
        """Detect language for syntax highlighting."""
        ext = path.split(".")[-1].lower() if "." in path else ""
        lang_map = {
            "zoya": "python",
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "json": "json",
            "yaml": "yaml",
            "yml": "yaml",
            "toml": "toml",
            "md": "markdown",
            "html": "html",
            "css": "css",
            "sql": "sql",
            "sh": "bash",
        }
        return lang_map.get(ext, "text")

    def get_editor_content(self) -> str:
        """Get current editor content."""
        editor = self.query_one("#editor-area", TextArea)
        return editor.text

    def save_current_tab(self):
        """Save current file."""
        if not self.current_file:
            return False

        content = self.get_editor_content()
        if hasattr(self.app, "file_manager"):
            success = self.app.file_manager.write_file(self.current_file, content)
            if success:
                self.query_one("#editor-status", Label).update(
                    f"💾 Saved: {self.current_file}"
                )
            return success
        return False

    def save_all_tabs(self) -> int:
        """Save all open tabs."""
        saved = 0
        for path, content in self.open_tabs.items():
            if hasattr(self.app, "file_manager"):
                if self.app.file_manager.write_file(path, content):
                    saved += 1
        return saved

    def close_current_tab(self):
        """Close current tab."""
        if self.current_file and self.current_file in self.open_tabs:
            del self.open_tabs[self.current_file]
            self.current_file = None
            editor = self.query_one("#editor-area", TextArea)
            editor.text = ""
            self.query_one("#editor-status", Label).update("No file open")

    def next_tab(self):
        """Switch to next tab (placeholder for Textual tab switching)."""
        pass

    def prev_tab(self):
        """Switch to previous tab (placeholder for Textual tab switching)."""
        pass

    def new_terminal(self):
        """Create a new terminal (uses existing terminal tab)."""
        self.query_one("#terminal-output", RichLog).write("[green]New terminal session started[/]")

    def toggle_terminal(self):
        """Toggle terminal visibility (switch to terminal tab)."""
        try:
            tabs = self.query_one("#center-tabs", TabbedContent)
            tabs.active = "tab-terminal"
        except Exception:
            pass

    def write_terminal(self, text: str):
        """Write to terminal output."""
        self.query_one("#terminal-output", RichLog).write(text)

    def write_build(self, text: str):
        """Write to build output."""
        self.query_one("#build-output", RichLog).write(text)

    def write_debug(self, text: str):
        """Write to debug output."""
        self.query_one("#debug-output", RichLog).write(text)

    def write_test(self, text: str):
        """Write to test output."""
        self.query_one("#test-output", RichLog).write(text)

    def write_log(self, text: str):
        """Write to log output."""
        self.query_one("#log-output", RichLog).write(text)
