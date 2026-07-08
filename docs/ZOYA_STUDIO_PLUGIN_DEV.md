# Zoya Studio Plugin Development

Zoya Studio supports installable plugins that extend the IDE with new commands, hooks, and UI elements.

## Plugin Structure

A plugin is a directory with:

```
my-plugin/
├── plugin.json      # Metadata
└── plugin.py        # Implementation
```

### plugin.json

```json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "A useful plugin",
  "author": "your-name",
  "entry": "plugin.py",
  "permissions": ["ui", "files", "ai"]
}
```

### plugin.py

```python
from zoya_studio.plugins.base import BasePlugin


class Plugin(BasePlugin):
    name = "my-plugin"
    version = "0.1.0"
    description = "A useful plugin"

    def activate(self) -> None:
        """Register commands when plugin loads."""
        self.register_command("hello", self.cmd_hello)
        self.register_hook("on_save", self.on_save)

    def deactivate(self) -> None:
        """Clean up when plugin unloads."""
        self.unregister_command("hello")

    def cmd_hello(self, *args) -> str:
        """Command handler. Returns a string result."""
        return "Hello from my-plugin!"

    def on_save(self, path: str) -> None:
        """Hook handler called on file save."""
        self.log(f"Saved: {path}")
```

## BasePlugin API

### Methods

| Method | Description |
|--------|-------------|
| `activate()` | Called on load. Register commands/hooks here. |
| `deactivate()` | Called on unload. Clean up here. |
| `register_command(name, handler)` | Register a `/command` |
| `unregister_command(name)` | Remove a command |
| `register_hook(hook, handler)` | Register a hook callback |
| `call_hook(hook, *args)` | Invoke all handlers for a hook |
| `log(message)` | Log to the app |

### Attributes

| Attribute | Description |
|-----------|-------------|
| `self.app` | The ZoyaStudioApp instance |
| `self.name` | Plugin name |
| `self.version` | Plugin version |
| `self.description` | Plugin description |

## Commands

Commands are invoked from the command bar with `/`:

```
/my-plugin:hello
```

Or if you register `hello`, just `/hello`.

Handler signature: `def cmd_name(self, *args) -> str`

## Hooks

Available hooks (call via `self.call_hook("hook_name", *args)`):

| Hook | Args | Called when |
|------|------|-------------|
| `on_save` | `path` | File saved |
| `on_open` | `path` | File opened |
| `on_project_open` | `project` | Project opened |
| `on_ai_message` | `message` | AI message sent |

## Permissions

Declare permissions in `plugin.json`:
- `ui` - Can modify UI
- `files` - Can read/write files
- `ai` - Can use AI
- `git` - Can run git
- `network` - Can make network requests

## Installation

```bash
# From a directory
cp -r my-plugin ~/.zoya/studio/plugins/

# From a zip
unzip my-plugin.zip -d ~/.zoya/studio/plugins/
```

Plugins are auto-loaded on startup if `plugins.auto_load` is enabled.

## Distribution

Package as a zip with `plugin.json` and `plugin.py` at the root:

```
my-plugin.zip
├── plugin.json
└── plugin.py
```

## Example: A Complete Plugin

```python
from zoya_studio.plugins.base import BasePlugin


class Plugin(BasePlugin):
    name = "todo"
    version = "1.0.0"
    description = "Simple todo list in AI memory"

    def activate(self) -> None:
        self.register_command("todo", self.cmd_todo)
        self.register_command("todos", self.cmd_todos)

    def deactivate(self) -> None:
        self.unregister_command("todo")
        self.unregister_command("todos")

    def cmd_todo(self, *args) -> str:
        if not args:
            return "Usage: /todo <task description>"
        task = " ".join(args)
        self.app.project_manager.add_task(task, priority="medium")
        return f"Added task: {task}"

    def cmd_todos(self, *args) -> str:
        memory = self.app.project_manager.get_memory()
        if not memory or not memory.tasks:
            return "No tasks"
        lines = []
        for t in memory.tasks:
            icon = "✓" if t.get("status") == "completed" else "○"
            lines.append(f"{icon} {t.get('title')}")
        return "\n".join(lines)
```
