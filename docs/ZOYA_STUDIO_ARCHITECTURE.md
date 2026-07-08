# Zoya Studio Architecture

## Overview

Zoya Studio is built with [Textual](https://textual.textualize.io/) for the TUI and [Rich](https://rich.readthedocs.io/) for rendering. The application is modular, fully typed, and cross-platform.

## Module Structure

```
zoya_studio/
├── __init__.py              # Package exports
├── __main__.py              # python -m zoya_studio entry
├── app.tcss                # Textual CSS theme
├── core/
│   ├── app.py              # ZoyaStudioApp + modal screens
│   ├── config.py          # Config system + theme presets
│   ├── project_manager.py # Project & memory management
│   ├── ai_manager.py      # AI providers (8) + streaming
│   ├── git_manager.py     # Git integration
│   ├── file_manager.py    # File operations
│   ├── package_manager.py # Package management
│   ├── templates.py       # Project templates
│   └── commands.py        # Command & natural language handler
├── widgets/
│   ├── sidebar_left.py    # Left sidebar
│   ├── sidebar_right.py   # AI workspace
│   ├── center_panel.py    # Editor/terminal/output
│   ├── bottom_bar.py      # Command/chat input
│   ├── status_bar.py      # Status bar
│   └── dialogs.py         # Modal dialogs
├── security/
│   └── crypto.py          # Encryption + credential store
├── plugins/
│   ├── __init__.py        # PluginManager
│   └── base.py            # BasePlugin ABC
├── settings/
│   └── __init__.py        # SettingsScreen
└── tests/                 # Unit & integration tests
```

## Core Components

### ZoyaStudioApp

The main application class. Extends `textual.app.App`. Responsibilities:
- Compose the UI (Header, StatusBar, Horizontal[left, center, right], BottomBar, Footer)
- Initialize all managers in `on_mount`
- Handle global keyboard bindings
- Route input (commands vs AI chat)
- Manage modal screens (command palette, quick open, global search, settings)

### Managers

Each manager is a plain class (not a widget) that holds state and business logic:

| Manager | Responsibility |
|---------|---------------|
| `ProjectManager` | Projects, favorites, memory |
| `AIManager` | AI providers, conversation |
| `GitManager` | Git operations |
| `FileManager` | File I/O, search |
| `PackageManager` | pip-based packages |
| `TemplateManager` | Project scaffolding |
| `PluginManager` | Plugin lifecycle |
| `CommandHandler` | Command parsing |
| `CryptoManager` | Encryption |
| `CredentialStore` | Secure key storage |

### Widgets

Widgets are Textual UI components:
- `LeftSidebar` - Projects/Files/Git/Search tabs
- `RightSidebar` - AI Workspace tabs
- `CenterPanel` - Editor/Terminal/Build/Debug/Tests/Logs
- `BottomBar` - Universal input
- `StatusBar` - Project/AI/Git status

## Data Flow

```
User Input (BottomBar)
    ↓
ZoyaStudioApp.on_input_submitted
    ↓
├── /command → CommandHandler.execute_command
└── natural language → AIManager.send_message (with context)
    ↓
Managers process request
    ↓
Widgets update (StatusBar, Sidebars, CenterPanel)
```

## AI Integration

`AIManager` uses a provider pattern. `BaseAIProvider` is an ABC with:
- `generate(prompt)` - single prompt
- `chat(messages)` - conversation
- `stream(messages)` - token streaming

Providers: OpenAI, Anthropic, Gemini, Ollama, LM Studio, OpenRouter, Custom, Mock.

All providers fall back to `MockProvider` if the API is unavailable and `use_local_fallback` is enabled.

API keys are stored encrypted via `CredentialStore` and `CryptoManager`.

## Configuration

Config is a nested dataclass stored as JSON at `~/.zoya/studio/config.json`. Theme presets are defined in `THEME_PRESETS`.

## Memory System

Project memory is stored in `.zoya/memory.json` within each project. It's loaded automatically on project open and updated as the user works.

## Security Model

- Credentials encrypted with Fernet (key at `~/.zoya/studio/secure/key.bin`)
- Destructive actions (delete, etc.) require confirmation via `ConfirmDialog`
- AI file modifications require user approval
- Local fallback prevents API key exposure when offline

## Testing Strategy

- Unit tests for each manager (config, crypto, file, ai, git, templates, commands, projects, plugins)
- Tests use `FakeApp` to avoid Textual runtime
- Run with: `python -m pytest tests/test_studio_*.py`

## Extensibility

- **Plugins**: Subclass `BasePlugin`, register commands/hooks
- **Templates**: Add to `TemplateManager.TEMPLATES`
- **Themes**: Add to `THEME_PRESETS`
- **Providers**: Subclass `BaseAIProvider`
