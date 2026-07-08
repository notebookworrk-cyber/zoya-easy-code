"""Configuration system for Zoya Studio."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class ThemeConfig:
    """Theme configuration."""
    name: str = "dark"
    background: str = "#0a0a1a"
    surface: str = "#1a1a3a"
    primary: str = "#00ff88"
    secondary: str = "#00aaff"
    accent: str = "#ff6b9d"
    text: str = "#e0e0e0"
    text_dim: str = "#888888"
    success: str = "#00ff88"
    warning: str = "#ffaa00"
    error: str = "#ff4444"
    border: str = "#2a2a5a"
    selection: str = "#00aaff44"


@dataclass
class UIConfig:
    """UI configuration."""
    show_left_sidebar: bool = True
    show_right_sidebar: bool = True
    show_status_bar: bool = True
    font_size: int = 14
    cursor_blink: bool = True
    line_numbers: bool = True
    word_wrap: bool = False
    minimap: bool = False


@dataclass
class EditorConfig:
    """Editor configuration."""
    tab_size: int = 4
    insert_spaces: bool = True
    auto_save: bool = False
    auto_save_delay: int = 1000
    format_on_save: bool = True
    trim_trailing_whitespace: bool = True
    insert_final_newline: bool = True


@dataclass
class AIConfig:
    """AI provider configuration."""
    provider: str = "openai"
    model: str = "gpt-4"
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = True
    use_local_fallback: bool = True
    systems_prompt: str = "You are Zoya Studio AI, an expert coding assistant for the Zoya language."


@dataclass
class GitConfig:
    """Git integration configuration."""
    enabled: bool = True
    user_name: str = ""
    user_email: str = ""
    default_branch: str = "main"
    auto_fetch: bool = False
    auto_stash: bool = False


@dataclass
class TerminalConfig:
    """Terminal configuration."""
    shell: str = ""
    font_size: int = 14
    cursor_blink: bool = True
    scrollback: int = 10000
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class PackageConfig:
    """Package manager configuration."""
    registry: str = "https://registry.zoya.dev"
    cache_dir: str = ""
    auto_update: bool = False
    verify_ssl: bool = True


@dataclass
class MemoryConfig:
    """Project memory configuration."""
    enabled: bool = True
    store_path: str = ""
    max_entries: int = 1000
    auto_summarize: bool = True


@dataclass
class PluginConfig:
    """Plugin system configuration."""
    enabled: bool = True
    directory: str = ""
    auto_load: bool = True
    marketplace: str = "https://plugins.zoya.dev"


@dataclass
class Config:
    """Main configuration."""
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    editor: EditorConfig = field(default_factory=EditorConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    git: GitConfig = field(default_factory=GitConfig)
    terminal: TerminalConfig = field(default_factory=TerminalConfig)
    packages: PackageConfig = field(default_factory=PackageConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)

    _config_path: Path | None = None

    @classmethod
    def load(cls, path: str | None = None) -> "Config":
        """Load configuration from file or create default."""
        if path is None:
            config_dir = Path.home() / ".zoya" / "studio"
            config_dir.mkdir(parents=True, exist_ok=True)
            path = str(config_dir / "config.json")

        config_path = Path(path)
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                config = cls.from_dict(data)
                config._config_path = config_path
                return config
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Failed to load config ({e}), using defaults")
                config = cls()
                config._config_path = config_path
                return config
        else:
            config = cls()
            config._config_path = config_path
            config.save()
            return config

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        config = cls()

        if "theme" in data:
            config.theme = ThemeConfig(**data["theme"])
        if "ui" in data:
            config.ui = UIConfig(**data["ui"])
        if "editor" in data:
            config.editor = EditorConfig(**data["editor"])
        if "ai" in data:
            config.ai = AIConfig(**data["ai"])
        if "git" in data:
            config.git = GitConfig(**data["git"])
        if "terminal" in data:
            config.terminal = TerminalConfig(**data["terminal"])
        if "packages" in data:
            config.packages = PackageConfig(**data["packages"])
        if "memory" in data:
            config.memory = MemoryConfig(**data["memory"])
        if "plugins" in data:
            config.plugins = PluginConfig(**data["plugins"])

        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "theme": asdict(self.theme),
            "ui": asdict(self.ui),
            "editor": asdict(self.editor),
            "ai": asdict(self.ai),
            "git": asdict(self.git),
            "terminal": asdict(self.terminal),
            "packages": asdict(self.packages),
            "memory": asdict(self.memory),
            "plugins": asdict(self.plugins),
        }

    def save(self, path: str | None = None) -> None:
        """Save configuration to file."""
        if path is None:
            path = self._config_path
        if path is None:
            config_dir = Path.home() / ".zoya" / "studio"
            config_dir.mkdir(parents=True, exist_ok=True)
            path = config_dir / "config.json"

        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        self._config_path = config_path

    def reset(self) -> None:
        """Reset to defaults."""
        defaults = Config()
        self.__dict__.update(defaults.__dict__)
        if self._config_path:
            self.save()

    def get(self, key: str, default: Any = None) -> Any:
        """Get nested config value."""
        parts = key.split(".")
        obj: Any = self
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                return default
        return obj

    def set(self, key: str, value: Any) -> None:
        """Set nested config value."""
        parts = key.split(".")
        obj: Any = self
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                setattr(obj, part, {})
                obj = getattr(obj, part)

        last = parts[-1]
        if hasattr(obj, last):
            setattr(obj, last, value)
        elif isinstance(obj, dict):
            obj[last] = value
        else:
            setattr(obj, last, value)

        self.save()


# Theme presets
THEME_PRESETS = {
    "dark": ThemeConfig(
        name="dark",
        background="#0a0a1a",
        surface="#1a1a3a",
        primary="#00ff88",
        secondary="#00aaff",
        accent="#ff6b9d",
        text="#e0e0e0",
        text_dim="#888888",
        success="#00ff88",
        warning="#ffaa00",
        error="#ff4444",
        border="#2a2a5a",
        selection="#00aaff44",
    ),
    "light": ThemeConfig(
        name="light",
        background="#ffffff",
        surface="#f5f5f5",
        primary="#008855",
        secondary="#0066cc",
        accent="#cc0077",
        text="#1a1a1a",
        text_dim="#666666",
        success="#008855",
        warning="#cc8800",
        error="#cc0000",
        border="#cccccc",
        selection="#0066cc44",
    ),
    "midnight": ThemeConfig(
        name="midnight",
        background="#0d1117",
        surface="#161b22",
        primary="#58a6ff",
        secondary="#79c0ff",
        accent="#ff7b72",
        text="#c9d1d9",
        text_dim="#8b949e",
        success="#3fb950",
        warning="#d29922",
        error="#f85149",
        border="#30363d",
        selection="#58a6ff44",
    ),
    "solarized": ThemeConfig(
        name="solarized",
        background="#002b36",
        surface="#073642",
        primary="#859900",
        secondary="#268bd2",
        accent="#d33682",
        text="#93a1a1",
        text_dim="#586e75",
        success="#859900",
        warning="#b58900",
        error="#dc322f",
        border="#586e75",
        selection="#268bd244",
    ),
    "dracula": ThemeConfig(
        name="dracula",
        background="#282a36",
        surface="#44475a",
        primary="#50fa7b",
        secondary="#8be9fd",
        accent="#ff79c6",
        text="#f8f8f2",
        text_dim="#6272a4",
        success="#50fa7b",
        warning="#f1fa8c",
        error="#ff5555",
        border="#44475a",
        selection="#bd93f944",
    ),
}
