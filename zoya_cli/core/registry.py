"""Command registry and discovery.

The registry is the single source of truth for the command tree. Built-in
commands register themselves at import time; plugins register additional nodes
at load time. The dispatcher reads the registry to parse argv and render help.
"""

from __future__ import annotations

from typing import Callable, Dict, Iterable, List

from zoya_cli.commands.base import Command


class CommandRegistry:
    """A tree of commands rooted at a synthetic ``zoya`` node."""

    def __init__(self) -> None:
        self.root = Command(name="zoya", help="Zoya CLI", description="")
        #: Mapping of plugin name -> list of registered command names.
        self._plugins: Dict[str, List[str]] = {}

    # -------------------------------------------------------------- register
    def register(self, command: Command, *, parent: str | None = None) -> None:
        """Register a command, optionally under a group by name."""
        target = self.root if parent is None else self._find(self.root, parent)
        if target is None:
            raise KeyError(f"Parent command group '{parent}' not found")
        if target.get_subcommand(command.name):
            # Allow re-registration (plugins may reload); replace in place.
            target.subcommands = [c for c in target.subcommands if c.name != command.name]
        target.add_command(command)

    def register_plugin_commands(self, plugin: str, commands: Iterable[Command]) -> None:
        names: List[str] = []
        for cmd in commands:
            self.register(cmd)
            names.append(cmd.name)
        self._plugins.setdefault(plugin, []).extend(names)

    # ---------------------------------------------------------------- lookup
    def _find(self, node: Command, name: str) -> Command | None:
        if node.name == name:
            return node
        for sub in node.subcommands:
            found = self._find(sub, name)
            if found is not None:
                return found
        return None

    def get(self, path: List[str]) -> Command | None:
        """Resolve a command by its path of names (e.g. ``["ai", "chat"]``)."""
        node = self.root
        for segment in path:
            nxt = node.get_subcommand(segment)
            if nxt is None:
                return None
            node = nxt
        return node

    def top_level(self) -> List[Command]:
        return [c for c in self.root.subcommands if not c.hidden]

    def plugin_commands(self, plugin: str) -> List[str]:
        return list(self._plugins.get(plugin, []))

    def list_plugins(self) -> Dict[str, List[str]]:
        return dict(self._plugins)

    # ----------------------------------------------------------- introspection
    def all_leaf_commands(self) -> List[Command]:
        out: List[Command] = []

        def walk(node: Command) -> None:
            if node.is_leaf() and node.name != "zoya":
                out.append(node)
            for sub in node.subcommands:
                walk(sub)

        walk(self.root)
        return out


#: Process-wide registry. Built once and shared across the CLI.
registry = CommandRegistry()


def register(command: Command, *, parent: str | None = None) -> Command:
    """Convenience decorator/function used by command modules."""
    registry.register(command, parent=parent)
    return command


def register_fn(
    name: str,
    help: str,
    run: Callable,
    *,
    arguments: Iterable = (),
    options: Iterable = (),
    parent: str | None = None,
    examples: Iterable[str] = (),
    description: str = "",
) -> Command:
    """Helper to build and register a simple leaf command in one call."""
    cmd = Command(
        name=name,
        help=help,
        description=description or help,
        arguments=list(arguments),
        options=list(options),
        examples=list(examples),
        run=run,
    )
    registry.register(cmd, parent=parent)
    return cmd
