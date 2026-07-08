"""Right sidebar widget for Zoya Studio - AI Workspace."""

from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import Button, Label, ListItem, ListView, RichLog, Static, TabbedContent, TabPane, Input


class RightSidebar(Vertical):
    """Right sidebar with AI workspace."""

    DEFAULT_CSS = """
    RightSidebar {
        width: 40;
        background: #161b22;
        border-left: solid #30363d;
    }

    #ai-header {
        height: 3;
        content-align: center middle;
        background: #0d1117;
        text-style: bold;
        color: #bc8cff;
    }

    #ai-conversation {
        height: 1fr;
        border: solid #30363d;
        margin: 0 1;
    }

    .ai-section-title {
        text-style: bold;
        color: #8b949e;
        padding: 1 1 0 1;
    }

    #ai-suggestions {
        height: 8;
    }

    #ai-tasks {
        height: 6;
    }

    Button.ai-btn {
        width: 1fr;
        margin: 0 1;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self):
        yield Label("🤖  AI WORKSPACE", id="ai-header")

        with TabbedContent(id="ai-tabs"):
            with TabPane("Chat", id="tab-chat"):
                yield RichLog(id="ai-conversation", markup=True, highlight=True, wrap=True)
                yield Input(placeholder="Ask AI or type a command...", id="ai-input")
                yield Button("Send", id="btn-ai-send", variant="primary", classes="ai-btn")

            with TabPane("Memory", id="tab-memory"):
                yield Label("Project Memory", classes="ai-section-title")
                yield Static("No project open", id="memory-info")

            with TabPane("Tasks", id="tab-tasks"):
                yield Label("Task List", classes="ai-section-title")
                yield ListView(id="ai-tasks")

            with TabPane("Docs", id="tab-docs"):
                yield Label("Documentation", classes="ai-section-title")
                yield ListView(id="ai-docs")

            with TabPane("Errors", id="tab-errors"):
                yield Label("Errors & Fixes", classes="ai-section-title")
                yield ListView(id="ai-errors")

    def on_mount(self):
        if hasattr(self.app, "ai_manager"):
            conv = self.app.ai_manager.get_conversation()
            log = self.query_one("#ai-conversation", RichLog)
            for msg in conv:
                if msg.role == "system":
                    continue
                prefix = "[yellow]You:[/]" if msg.role == "user" else "[green]AI:[/]"
                log.write(f"{prefix} {msg.content}")

    def add_message(self, role: str, content: str):
        """Add a message to the conversation log."""
        log = self.query_one("#ai-conversation", RichLog)
        prefix = "[yellow]You:[/]" if role == "user" else "[green]AI:[/]"
        log.write(f"{prefix} {content}")
        log.scroll_end()

    def stream_message(self, chunk: str):
        """Stream a message chunk."""
        log = self.query_one("#ai-conversation", RichLog)
        log.write(chunk)

    def refresh_memory(self):
        """Refresh project memory display."""
        if not hasattr(self.app, "project_manager"):
            return

        pm = self.app.project_manager
        memory = pm.get_memory()

        if not memory:
            self.query_one("#memory-info", Static).update("No project memory yet")
            return

        lines = []
        if memory.architecture:
            lines.append(f"Architecture: {memory.architecture[:100]}")
        if memory.goals:
            lines.append(f"Goals: {len(memory.goals)} defined")
        if memory.tasks:
            lines.append(f"Tasks: {len(memory.tasks)} total")
        if memory.open_bugs:
            lines.append(f"Open bugs: {len(memory.open_bugs)}")

        self.query_one("#memory-info", Static).update("\n".join(lines) or "Memory loaded")

    def refresh_tasks(self):
        """Refresh task list."""
        if not hasattr(self.app, "project_manager"):
            return

        pm = self.app.project_manager
        memory = pm.get_memory()

        task_list = self.query_one("#ai-tasks", ListView)
        task_list.clear()

        if not memory:
            return

        for task in memory.tasks[-20:]:
            status_icon = "✓" if task.get("status") == "completed" else "○"
            task_list.append(ListItem(
                Static(f"{status_icon} {task.get('title', 'Unknown')}"),
            ))

    def refresh_errors(self):
        """Refresh errors list."""
        error_list = self.query_one("#ai-errors", ListView)
        error_list.clear()
        error_list.append(ListItem(Static("No errors detected")))

    def refresh_docs(self):
        """Refresh documentation list."""
        doc_list = self.query_one("#ai-docs", ListView)
        doc_list.clear()
        doc_list.append(ListItem(Static("📘 Getting Started")))
        doc_list.append(ListItem(Static("📘 Zoya Language Reference")))
        doc_list.append(ListItem(Static("📘 AI Provider Setup")))
        doc_list.append(ListItem(Static("📘 Plugin Development")))
