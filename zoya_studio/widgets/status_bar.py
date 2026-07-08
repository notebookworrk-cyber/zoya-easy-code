"""Status bar widget for Zoya Studio."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


class StatusBar(Horizontal):
    """Top status bar with connection indicator and project info."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: #0d1117;
        border-bottom: solid #30363d;
        align: left middle;
    }

    #status-project {
        width: 30;
        padding: 0 1;
        color: #58a6ff;
    }

    #status-ai {
        width: 25;
        padding: 0 1;
        color: #bc8cff;
    }

    #status-git {
        width: 20;
        padding: 0 1;
        color: #3fb950;
    }

    #status-line {
        width: 1fr;
        content-align: right middle;
        padding: 0 1;
        color: #8b949e;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("No project", id="status-project")
        yield Static("AI: mock", id="status-ai")
        yield Static("", id="status-git")
        yield Static("Zoya Studio v1.0.0", id="status-line")

    def set_project(self, name: str):
        """Set current project name."""
        self.query_one("#status-project", Static).update(f"📁 {name}")

    def set_ai_status(self, provider: str, model: str):
        """Set AI status."""
        self.query_one("#status-ai", Static).update(f"AI: {provider}")

    def set_git_status(self, branch: str, has_changes: bool):
        """Set git status."""
        indicator = "●" if has_changes else "○"
        text = f"⎇ {branch} {indicator}" if branch else ""
        self.query_one("#status-git", Static).update(text)

    def set_line_status(self, text: str):
        """Set right-side status text."""
        self.query_one("#status-line", Static).update(text)
