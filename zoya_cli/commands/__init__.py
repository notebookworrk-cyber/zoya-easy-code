"""Command registrations.

Call :func:`register_all` early in the CLI bootstrap to register every
built-in command in the global :class:`CommandRegistry`.
"""

from __future__ import annotations


def register_all() -> None:
    """Import and call every registration function."""
    from zoya_cli.commands.system import register_commands
    from zoya_cli.commands.ai import register_ai_commands
    from zoya_cli.commands.game import register_game_commands

    register_commands()
    register_ai_commands()
    register_game_commands()
