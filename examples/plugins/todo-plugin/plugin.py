"""Todo plugin for Zoya Studio.

Adds /todo and /todos commands that integrate with project memory.
"""

from zoya_studio.plugins.base import BasePlugin


class Plugin(BasePlugin):
    """Todo list plugin with project memory integration."""

    name = "todo"
    version = "1.0.0"
    description = "Simple todo list integrated with project memory"

    def activate(self) -> None:
        self.register_command("todo", self.cmd_todo)
        self.register_command("todos", self.cmd_todos)
        self.register_command("done", self.cmd_done)

    def deactivate(self) -> None:
        self.unregister_command("todo")
        self.unregister_command("todos")
        self.unregister_command("done")

    def cmd_todo(self, *args) -> str:
        """Add a todo: /todo <description>"""
        if not args:
            return "Usage: /todo <task description>"
        task = " ".join(args)
        self.app.project_manager.add_task(task, priority="medium")
        return f"✓ Added task: {task}"

    def cmd_todos(self, *args) -> str:
        """List all todos: /todos"""
        memory = self.app.project_manager.get_memory()
        if not memory or not memory.tasks:
            return "No tasks yet. Use /todo <description> to add one."
        lines = ["📋 Tasks:"]
        for t in memory.tasks:
            icon = "✓" if t.get("status") == "completed" else "○"
            priority = t.get("priority", "medium")
            lines.append(f"  {icon} [{priority}] {t.get('title')}")
        return "\n".join(lines)

    def cmd_done(self, *args) -> str:
        """Mark a todo complete: /done <description>"""
        if not args:
            return "Usage: /done <task description>"
        title = " ".join(args)
        self.app.project_manager.complete_task(title)
        return f"✓ Completed: {title}"
