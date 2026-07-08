# Zoya Studio

**AI-Powered Terminal IDE for the Zoya Programming Language**

Launch with:
```bash
zoya studio
zoya-studio
python -m zoya_studio
```

## What It Is

Zoya Studio is a complete, full-screen terminal IDE built with [Textual](https://textual.textualize.io/). It brings together everything a Zoya developer needs in one polished interface:

- **Project management** — recent, favorites, templates, examples
- **Code editor** — syntax highlighting, line numbers, multiple tabs
- **Integrated terminal** — run commands without leaving the IDE
- **AI workspace** — conversational AI with project-aware context
- **Git tools** — status, commit, push, pull, branches
- **Package manager** — install/update/remove from the UI
- **Global search** — find files and content instantly
- **Command palette** — VS Code-style command palette
- **Themes** — dark, light, midnight, solarized, dracula
- **Plugins** — extensible plugin system
- **Security** — encrypted credential storage

## Architecture

```
zoya_studio/
├── core/
│   ├── app.py              # Main app + modal screens
│   ├── config.py          # Config + themes
│   ├── project_manager.py # Projects + memory
│   ├── ai_manager.py      # AI providers
│   ├── git_manager.py     # Git integration
│   ├── file_manager.py    # File operations
│   ├── package_manager.py # Package management
│   ├── templates.py       # Project templates
│   └── commands.py        # Command handler
├── widgets/
│   ├── sidebar_left.py    # Left panel
│   ├── sidebar_right.py   # AI workspace
│   ├── center_panel.py    # Editor/terminal
│   ├── bottom_bar.py      # Command input
│   ├── status_bar.py      # Status
│   └── dialogs.py         # Modal dialogs
├── security/
│   └── crypto.py          # Encryption
├── plugins/
│   ├── __init__.py        # PluginManager
│   └── base.py            # BasePlugin
├── settings/
│   └── __init__.py        # SettingsScreen
├── app.tcss                # Styles
└── tests/                 # Unit + integration tests
```

## Features in Detail

### Multi-Provider AI

| Provider | Requires |
|----------|----------|
| OpenAI | `openai` + key |
| Anthropic | `anthropic` + key |
| Google Gemini | `google-generativeai` + key |
| Ollama | Local Ollama |
| LM Studio | Local LM Studio |
| OpenRouter | `openai` + key |
| Custom | OpenAI-compatible URL |
| Mock | Built-in, no key |

API keys are encrypted at rest with Fernet. See [docs/ZOYA_STUDIO_AI_PROVIDERS.md](../docs/ZOYA_STUDIO_AI_PROVIDERS.md).

### Project Memory

Each project auto-maintains memory in `.zoya/memory.json`:
- Architecture, coding style, goals
- Tasks (with status)
- Completed work, open bugs
- Important files, user preferences
- Conversation history, notes

Loaded automatically on project open. See [docs/ZOYA_STUDIO_MEMORY.md](../docs/ZOYA_STUDIO_MEMORY.md).

### Plugins

```python
from zoya_studio.plugins.base import BasePlugin

class Plugin(BasePlugin):
    name = "my-plugin"
    version = "0.1.0"

    def activate(self):
        self.register_command("hello", self.cmd_hello)

    def deactivate(self):
        self.unregister_command("hello")

    def cmd_hello(self, *args):
        return "Hello from my plugin!"
```

See [docs/ZOYA_STUDIO_PLUGIN_DEV.md](../docs/ZOYA_STUDIO_PLUGIN_DEV.md).

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Q` | Quit |
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+B` | Toggle Sidebar |
| `Ctrl+Shift+B` | Toggle AI Panel |
| `Ctrl+\`` | Toggle Terminal |
| `Ctrl+P` | Quick Open |
| `Ctrl+Shift+F` | Global Search |
| `Ctrl+S` | Save |
| `Ctrl+Shift+S` | Save All |
| `F5` | Run |
| `F6` | Debug |
| `Ctrl+Shift+T` | New Terminal |
| `Ctrl+W` | Close Tab |
| `F1` | Settings |

## Commands

Type in the bottom bar:

```
/help              Show all commands
/new <name>       Create project
/open <path>      Open project
/run               Run project
/build             Build project
/test              Run tests
/git commit "msg"  Commit changes
/install <pkg>    Install package
/update            Update packages
/template <name>  New from template
/theme <name>     Change theme
/memory            Show project memory
/ai explain       Explain current file
/ai fix           Fix errors in current file
/clear             Clear chat
```

Or just type naturally:
```
Create a 3D zombie game.
Fix all parser errors.
Optimize my compiler.
Explain this code.
```

## Testing

```bash
python -m pytest tests/test_studio_*.py -v
```

52 tests covering config, crypto, file manager, AI manager, templates, commands, project manager, plugins, and integration.

## License

MIT

---

Built for the Zoya Easy Code platform.
