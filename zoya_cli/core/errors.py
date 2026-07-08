"""Typed error hierarchy for the Zoya CLI.

Every user-facing failure in the CLI should raise a :class:`ZoyaError` subclass.
The top-level dispatcher catches these and renders a friendly, actionable
message instead of a raw traceback. Internal programming errors are allowed to
propagate when ``--debug`` is enabled.
"""

from __future__ import annotations

from typing import Iterable


class ZoyaError(Exception):
    """Base class for all expected, user-facing CLI errors."""

    #: Exit code used when this error is the top-level failure.
    exit_code: int = 1

    #: Short, human readable summary shown in bold.
    title: str = "Command failed"

    def __init__(
        self,
        message: str,
        *,
        hints: Iterable[str] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        #: Actionable remediation suggestions.
        self.hints: list[str] = list(hints or [])
        if cause is not None:
            self.__cause__ = cause

    def add_hint(self, hint: str) -> ZoyaError:
        self.hints.append(hint)
        return self


class UsageError(ZoyaError):
    """Raised when the user invokes a command incorrectly (bad args)."""

    exit_code = 2
    title = "Invalid usage"


class CommandNotFoundError(ZoyaError):
    """Raised when an unknown command is invoked."""

    exit_code = 2
    title = "Unknown command"

    def __init__(self, command: str, suggestions: Iterable[str] | None = None) -> None:
        self.command = command
        self.suggestions = list(suggestions or [])
        message = f"Command '{command}' is not recognized by Zoya."
        super().__init__(message)


class ConfigError(ZoyaError):
    """Raised on invalid configuration files or values."""

    exit_code = 3
    title = "Configuration error"


class ProjectError(ZoyaError):
    """Raised when an operation requires a Zoya project but none is found."""

    exit_code = 4
    title = "Project error"


class BuildError(ZoyaError):
    """Raised when a build/compile step fails."""

    exit_code = 5
    title = "Build failed"


class TestError(ZoyaError):
    """Raised when the test suite reports failures."""

    exit_code = 6
    title = "Tests failed"


class PackageError(ZoyaError):
    """Raised on package-manager failures (resolution, integrity, network)."""

    exit_code = 7
    title = "Package error"


class PluginError(ZoyaError):
    """Raised on plugin lifecycle failures."""

    exit_code = 8
    title = "Plugin error"


class AIError(ZoyaError):
    """Raised on AI provider failures."""

    exit_code = 9
    title = "AI provider error"


class GameError(ZoyaError):
    """Raised on game-engine failures."""

    exit_code = 10
    title = "Game error"


class EnvironmentError_(ZoyaError):
    """Raised when the host environment is missing required tooling."""

    exit_code = 11
    title = "Environment error"
