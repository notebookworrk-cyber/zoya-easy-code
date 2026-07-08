# Zoya Studio

**AI-Powered Terminal IDE for the Zoya Programming Language**

Zoya Studio is a complete, full-screen terminal-based IDE for Zoya development. It combines project management, coding, AI assistance, package management, Git tools, and developer workflows into a single unified application launched with one command.

## Quick Start

```bash
# Install
pip install -e .

# Launch
zoya studio
# or
zoya-studio
# or
python -m zoya_studio
```

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Zoya Studio                                            Connected ● │
├──────────────┬──────────────────────────────┬────────────────────┤
│ Projects     │ Editor / Console             │ AI Workspace       │
│              │                              │                    │
│ 📁 Game      │ Current file                 │ Conversation       │
│ 📁 AI Bot    │ Terminal                     │ Memory             │
│ 📁 Website   │ Build output                 │ Suggestions        │
│              │ Logs                         │ Documentation      │
├──────────────┴──────────────────────────────┴────────────────────┤
│ Command / Chat Input                                           Send │
└──────────────────────────────────────────────────────────────────┘
```

## Features

### Left Sidebar
- **Projects**: Recent, Favorites, Templates, Examples
- **Files**: Built-in file explorer with create/rename/delete
- **Git**: Status, commit, push, pull, branch
- **Search**: File and content search

### Center Panel
- **Editor**: Syntax highlighting, line numbers, tabs
- **Terminal**: Integrated terminal output
- **Build**: Compiler/build output
- **Debug**: Debug console
- **Tests**: Test results
- **Logs**: Application logs

### Right Sidebar (AI Workspace)
- **Chat**: Conversational AI with streaming
- **Memory**: Project memory (architecture, goals, tasks, bugs)
- **Tasks**: Task list
- **Docs**: Documentation browser
- **Errors**: Errors and suggested fixes

### Bottom Input Bar
Universal command/chat bar. Type natural language or commands:

```
Create a 3D zombie game.
Fix all parser errors.
Optimize my compiler.
/help
/new myproject
/run
/git commit "Initial commit"
```

## AI Providers

Zoya Studio supports multiple AI providers, all configurable in Settings (F1):

- OpenAI
- Anthropic (Claude)
- Google Gemini
- Ollama (local)
- LM Studio (local)
- OpenRouter
- Custom OpenAI-compatible APIs
- Mock (no API key, built-in fallback)

API keys are encrypted at rest using Fernet encryption.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Q` | Quit |
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+B` | Toggle Left Sidebar |
| `Ctrl+Shift+B` | Toggle AI Panel |
| `Ctrl+\`` | Toggle Terminal |
| `Ctrl+P` | Quick Open |
| `Ctrl+Shift+F` | Global Search |
| `Ctrl+S` | Save File |
| `Ctrl+Shift+S` | Save All |
| `F5` | Run Project |
| `F6` | Debug |
| `Ctrl+Shift+T` | New Terminal |
| `Ctrl+W` | Close Tab |
| `F1` | Settings |

## Project Memory

Each project automatically maintains memory in `.zoya/memory.json`:

- Architecture
- Coding style
- Goals
- Tasks (with status)
- Completed work
- Open bugs
- Important files
- User preferences
- Conversation history
- Notes

Memory is loaded automatically when a project is opened.

## Git Integration

Full Git support:

- Status (with summary counts)
- Commit
- Push / Pull
- Branch create/checkout
- Diff
- Log / history
- Stash
- Merge
- Conflict resolution

## Package Manager

Install, update, and remove packages directly:

```
/install requests
/uninstall old-package
/update
```

Dependencies are tracked in `zoya.toml`.

## Templates

Create projects from templates:

- Console App
- 2D Game
- 3D Game
- AI Assistant
- Desktop App
- Web API
- Library
- Plugin

```
/template console-app myapp
```

## Themes

Built-in themes: Dark, Light, Midnight, Solarized, Dracula.
Switch with `Ctrl+T` or in Settings.

## Settings

Configure everything: AI provider, theme, editor, git, packages, privacy.
Settings are stored at `~/.zoya/studio/config.json`.

## Plugins

Install plugins to extend Zoya Studio. See [Plugin Development](PLUGIN_DEV.md).

```python
from zoya_studio.plugins.base import BasePlugin

class Plugin(BasePlugin):
    name = "my-plugin"
    version = "0.1.0"
    description = "A useful plugin"

    def activate(self):
        self.register_command("hello", self.cmd_hello)

    def deactivate(self):
        self.unregister_command("hello")

    def cmd_hello(self, *args):
        return "Hello from my plugin!"
```

## Security

- API keys encrypted with Fernet at rest
- Destructive actions require confirmation
- AI-generated file modifications require user approval
- Local AI fallback when no provider configured

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Testing

```bash
python -m pytest tests/test_studio_*.py -v
```

## Requirements

- Python 3.11+
- textual >= 8.0.0
- typer >= 0.12.0
- rich >= 13.0.0
- cryptography >= 42.0.0 (for credential encryption)

Optional: openai, anthropic, google-generativeai for real AI providers.
