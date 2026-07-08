"""Base plugin class for Zoya Studio."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable


class BasePlugin(ABC):
    """Base class for plugins.

    Plugins should subclass this and implement activate() and deactivate().
    Register commands with register_command() and hooks with register_hook().

    Example:
        ```python
        from zoya_studio.plugins.base import BasePlugin

        class Plugin(BasePlugin):
            name = "my-plugin"
            version = "0.1.0"
            description = "A useful plugin"

            def activate(self) -> None:
                self.register_command("hello", self.cmd_hello)

            def deactivate(self) -> None:
                self.unregister_command("hello")

            def cmd_hello(self, args: list[str]) -> str:
                return "Hello from my plugin!"
        ```
    """

    name: str = "unknown"
    version: str = "0.0.0"
    description: str = ""

    def __init__(self, app: Any):
        self.app = app
        self._commands: dict[str, Callable] = {}
        self._hooks: dict[str, list[Callable]] = {}

    @abstractmethod
    def activate(self) -> None:
        """Called when the plugin is activated. Register commands/hooks here."""
        raise NotImplementedError

    @abstractmethod
    def deactivate(self) -> None:
        """Called when the plugin is deactivated. Unregister commands/hooks here."""
        raise NotImplementedError

    def register_command(self, name: str, handler: Callable) -> None:
        """Register a command handler.

        Args:
            name: Command name (without slash).
            handler: Callable that takes optional args and returns a string.
        """
        self._commands[name] = handler

    def unregister_command(self, name: str) -> None:
        """Unregister a command handler."""
        self._commands.pop(name, None)

    def register_hook(self, hook: str, handler: Callable) -> None:
        """Register a hook callback.

        Args:
            hook: Hook name (e.g., 'on_save', 'on_open').
            handler: Callable invoked when the hook fires.
        """
        if hook not in self._hooks:
            self._hooks[hook] = []
        self._hooks[hook].append(handler)

    def call_hook(self, hook: str, *args: Any, **kwargs: Any) -> list[Any]:
        """Call all handlers registered for a hook."""
        results = []
        for handler in self._hooks.get(hook, []):
            results.append(handler(*args, **kwargs))
        return results

    def log(self, message: str) -> None:
        """Log a message to the application."""
        if hasattr(self.app, "log"):
            self.app.log(f"[{self.name}] {message}")
