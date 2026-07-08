# Zoya Studio Memory System

Zoya Studio maintains persistent memory for each project to provide context-aware AI assistance and track project state.

## Storage

Memory is stored in `.zoya/memory.json` within each project directory. It's loaded automatically when a project is opened and saved whenever it changes.

## Structure

```json
{
  "architecture": "Modular MVC with separate engine and UI layers",
  "coding_style": "Type hints, docstrings, small functions",
  "goals": ["Ship v1.0", "Add multiplayer"],
  "tasks": [
    {
      "title": "Implement auth",
      "status": "pending",
      "priority": "high",
      "created": "2024-01-01T00:00:00"
    }
  ],
  "completed_work": ["Set up CI", "Write tests"],
  "open_bugs": ["Crash on exit", "Memory leak in renderer"],
  "important_files": ["src/main.zoya", "src/engine.zoya"],
  "user_preferences": {"theme": "dark", "indent": 4},
  "conversations": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."}
  ],
  "notes": ["Remember to optimize hot loop"],
  "updated": "2024-01-01T00:00:00"
}
```

## API

### ProjectManager methods

| Method | Description |
|--------|-------------|
| `get_memory()` | Get current project memory |
| `update_memory(**kwargs)` | Update memory fields |
| `add_conversation(role, content)` | Add chat message |
| `add_task(title, status, priority)` | Add a task |
| `complete_task(title)` | Mark task completed |
| `add_bug(description)` | Add open bug |
| `resolve_bug(description)` | Resolve a bug |
| `add_note(note)` | Add a note |
| `save_memory()` | Persist to disk |

## Usage in AI

When you chat with AI, the memory is automatically included as context:

```
Context:
Project: mygame
Architecture: Modular MVC
Goals: Ship v1.0, Add multiplayer
Current file: src/main.zoya
```

This helps the AI understand your project without re-explaining each time.

## Memory in UI

The right sidebar "Memory" tab shows:
- Architecture summary
- Goals count
- Tasks count
- Open bugs count

The "Tasks" tab shows the full task list with completion status.

## Best Practices

1. Let Zoya Studio track tasks as you work
2. Use `/memory` to review current state
3. Add notes for important context the AI should remember
4. Memory is auto-saved—no manual export needed
