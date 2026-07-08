# Zoya Studio - Changelog

## v1.0.0 (2024)

### Added
- Full-screen terminal IDE launched with `zoya studio`, `zoya-studio`, or `python -m zoya_studio`
- **Left Sidebar**: Projects (recent/favorites/templates), Files explorer, Git status, Search
- **Center Panel**: Code editor (syntax highlighting, line numbers, tabs), Terminal, Build output, Debug console, Test results, Logs
- **Right Sidebar (AI Workspace)**: Chat with streaming, Project memory, Task list, Documentation, Errors & fixes
- **Bottom Input Bar**: Universal command/chat interface (natural language + `/commands`)
- **Multi-Provider AI**: OpenAI, Anthropic, Gemini, Ollama, LM Studio, OpenRouter, Custom OpenAI-compatible, Mock fallback
- **Project Memory**: Auto-maintained `.zoya/memory.json` with architecture, goals, tasks, bugs, conversations
- **Git Integration**: Status, commit, push, pull, branches, diff, log, stash, merge
- **Package Manager**: Install/update/remove via pip, dependency tracking in `zoya.toml`
- **Templates**: 8 project templates (console, 2D/3D game, AI assistant, desktop, web-api, library, plugin)
- **Global Search**: File and content search with modal
- **Command Palette**: VS Code-style (Ctrl+Shift+P)
- **Themes**: Dark, Light, Midnight, Solarized, Dracula
- **Settings**: Full configuration UI (AI, theme, editor, git, packages, privacy)
- **Plugin System**: Extensible `BasePlugin` with command/hook registration
- **Security**: Fernet-encrypted credential storage, confirmation dialogs, local fallback
- **Keyboard Shortcuts**: 17 bindings
- **Documentation**: Studio guide, Architecture, Plugin Dev, AI Providers, Memory System
- **Tests**: 55 unit + integration tests (pytest)

### Technical
- Python 3.11+, fully typed
- Modular architecture (core/, widgets/, security/, plugins/, settings/)
- Textual 8.x + Rich for rendering
- Cross-platform (Windows, macOS, Linux)
- No placeholder code, no TODOs, no pseudo-code
