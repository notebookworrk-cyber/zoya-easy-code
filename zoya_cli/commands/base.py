"""Command model and base types for the Zoya CLI.

A command is a small, declarative node in a tree. The dispatcher walks the tree
to parse argv, then invokes :meth:`Command.run`. Plugins extend the CLI simply
by registering additional :class:`Command` nodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from typing import Any, Callable, Mapping, Sequence

from zoya_cli.core.errors import UsageError


class OptionAction(str, Enum):
    STORE = "store"
    STORE_TRUE = "store_true"
    STORE_FALSE = "store_false"
    COUNT = "count"
    APPEND = "append"


@dataclass(frozen=True)
class Option:
    """Declarative specification of a command-line flag."""

    long: str  # "--verbose"
    short: str | None = None  # "-v"
    help: str = ""
    action: OptionAction = OptionAction.STORE
    default: Any = None
    metavar: str | None = None
    choices: Sequence[str] | None = None
    env_var: str | None = None
    value_type: type = str


@dataclass(frozen=True)
class Argument:
    """Declarative specification of a positional argument."""

    name: str
    help: str = ""
    nargs: int = 1  # 1 = exactly one, 0..n via special handling below
    metavar: str | None = None
    default: Any = None


@dataclass
class Command:
    """A single CLI command or command group."""

    name: str
    help: str = ""
    description: str = ""
    options: list[Option] = field(default_factory=list)
    arguments: list[Argument] = field(default_factory=list)
    subcommands: list["Command"] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    #: Optional handler. Command groups may omit it.
    run: Callable[["Context"], int | None] | None = None
    #: Whether to allow arbitrary trailing positionals (passthrough).
    allow_unknown_args: bool = False
    #: Hidden commands are not shown in help but still runnable.
    hidden: bool = False
    #: Plugin that registered this command (for provenance in `zoya plugin list`).
    plugin: str | None = None

    def add_option(self, opt: Option) -> "Command":
        self.options.append(opt)
        return self

    def add_argument(self, arg: Argument) -> "Command":
        self.arguments.append(arg)
        return self

    def add_command(self, cmd: "Command") -> "Command":
        self.subcommands.append(cmd)
        return self

    def get_subcommand(self, name: str) -> "Command | None":
        for sub in self.subcommands:
            if sub.name == name:
                return sub
        return None

    def is_leaf(self) -> bool:
        return self.run is not None

    def merged_options(self) -> list[Option]:
        """Options declared on this command (for dispatch)."""
        return self.options

    def option_index(self) -> dict[str, Option]:
        idx: dict[str, Option] = {}
        for opt in self.options:
            idx[opt.long] = opt
            if opt.short:
                idx[opt.short] = opt
        return idx


@dataclass
class Context:
    """Runtime context passed to every command handler."""

    #: Parsed long-option values (e.g. ``verbose`` -> True).
    opts: dict[str, Any]
    #: Parsed positional arguments in order.
    args: list[str]
    #: Full resolved command path, e.g. ``["ai", "chat"]``.
    command_path: list[str]
    #: Rich console wrapper (see :mod:`zoya_cli.term.console`).
    console: Any
    #: UI helpers (progress, tables, prompts).
    ui: Any
    #: Merged configuration.
    config: Any
    #: Project root if inside a project, else ``None``.
    project_root: Path | None
    #: Whether ``--debug`` was requested.
    debug: bool
    #: Extra raw argv after ``--`` (passthrough).
    remainder: list[str] = field(default_factory=list)

    def require_project(self) -> Path:
        if self.project_root is None:
            from zoya_cli.core.errors import ProjectError

            raise ProjectError(
                "This command must be run inside a Zoya project.",
                hints=["Run 'zoya init' to initialize a project here."],
            )
        return self.project_root

    def opt(self, long: str, default: Any = None) -> Any:
        return self.opts.get(long.lstrip("-"), default)

    def verbose(self) -> bool:
        return bool(self.opts.get("verbose", False))

    def quiet(self) -> bool:
        return bool(self.opts.get("quiet", False))

    def as_mapping(self) -> Mapping[str, Any]:
        return {"opts": self.opts, "args": self.args}
