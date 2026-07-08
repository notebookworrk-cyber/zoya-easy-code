"""Bottom input bar for Zoya Studio."""

from __future__ import annotations

from textual.containers import Horizontal
from textual.widgets import Button, Input, Static


class BottomBar(Horizontal):
    """Bottom universal command/chat bar."""

    DEFAULT_CSS = """
    BottomBar {
        height: 3;
        background: #0d1117;
        border-top: solid #30363d;
        align: left middle;
    }

    #command-input {
        width: 1fr;
        margin: 0 1;
    }

    #send-btn {
        width: 12;
        margin: 0 1;
    }

    #input-mode {
        width: 16;
        content-align: center middle;
        color: #8b949e;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = "chat"

    def compose(self):
        yield Static("💬 Chat", id="input-mode")
        yield Input(
            placeholder="Type a command or message... (e.g., 'Create a 3D zombie game')",
            id="command-input",
        )
        yield Button("Send", id="send-btn", variant="primary")

    def set_mode(self, mode: str):
        """Set input mode: chat or command."""
        self.mode = mode
        mode_label = self.query_one("#input-mode", Static)
        if mode == "command":
            mode_label.update("⚡ Command")
        else:
            mode_label.update("💬 Chat")

    def get_input(self) -> str:
        """Get input value."""
        return self.query_one("#command-input", Input).value

    def clear_input(self):
        """Clear input."""
        self.query_one("#command-input", Input).value = ""
