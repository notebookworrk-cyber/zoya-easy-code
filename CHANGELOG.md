# Changelog

All notable changes to Zoya will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-06-30

### Added
- Core interpreter (lexer, parser, AST, runtime)
- Interactive REPL with command history
- Variables, conditionals, loops, functions
- Lists and dictionaries with method support
- String interpolation (`f"..."`)
- Module/import system
- 15 standard library modules:
  - `math` — Math functions
  - `string` — String operations
  - `random` — Random generation
  - `time` — Time utilities
  - `file` — File I/O
  - `json` — JSON serialization
  - `network` — HTTP requests
  - `audio` — Audio playback
  - `physics` — 2D/3D physics
  - `game` — 2D game engine (pygame-ce)
  - `game3d` — 3D engine (Ursina)
  - `ai` — AI integration (Gemini, OpenAI, Ollama, LM Studio)
  - `csv` — CSV processing
  - `database` — SQLite wrapper
  - `collections` — Advanced data structures
- CLI with flags (`--repl`, `--version`, `--help`, `-c`)
- Comprehensive error messages with line numbers
- Package published to PyPI as `zoya-lang`
