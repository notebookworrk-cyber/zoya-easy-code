"""Zoya CLI - command dispatch engine.

Parses ``argv`` against the registered :class:`CommandRegistry`, builds a
:class:`Context`, renders rich help, and invokes the matched handler.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, List, Tuple

from zoya_cli._meta import __version__, __codename__
from zoya_cli.commands.base import Command, Context, Option, OptionAction
from zoya_cli.core.errors import ZoyaError, CommandNotFoundError, UsageError
from zoya_cli.core.config import Config, find_project_root
from zoya_cli.core.registry import registry
from zoya_cli.core.theme import theme_names
from zoya_cli.core.suggest import suggest, did_you_mean
from zoya_cli.commands import register_all
from zoya_cli.term.console import Console, get_console, set_console


def _build_options_map(cmd: Command) -> dict[str, Option]:
    idx: dict[str, Option] = {}
    for opt in cmd.options:
        idx[opt.long] = opt
        if opt.short:
            idx[opt.short] = opt
    return idx


def _walk_tree(argv: List[str]) -> Tuple[Command, List[str]]:
    node: Command = registry.root
    pos = 0
    while pos < len(argv):
        token = argv[pos]
        if token == "--":
            break
        if token.startswith("-"):
            break
        sub = node.get_subcommand(token)
        if sub is not None:
            node = sub
            pos += 1
        elif node.is_leaf():
            break
        else:
            suggestions = suggest(token, (c.name for c in node.subcommands if not c.hidden))
            raise CommandNotFoundError(command=token, suggestions=suggestions)
    return node, argv[pos:]


def _parse_options(
    cmd: Command, tokens: List[str], debug: bool = False
) -> Tuple[dict[str, Any], List[str], List[str]]:
    opts: dict[str, Any] = {}
    pos_args: List[str] = []
    remainder: List[str] = []
    opt_map = _build_options_map(cmd)
    i = 0
    for opt_spec in cmd.options:
        if opt_spec.action == OptionAction.STORE_TRUE:
            opts[opt_spec.long] = False
        elif opt_spec.action == OptionAction.STORE_FALSE:
            opts[opt_spec.long] = True
        elif opt_spec.action == OptionAction.COUNT:
            opts[opt_spec.long] = 0
        elif opt_spec.action == OptionAction.APPEND:
            opts[opt_spec.long] = []
        else:
            opts[opt_spec.long] = opt_spec.default if opt_spec.default is not None else None

    while i < len(tokens):
        token = tokens[i]
        if token == "--":
            remainder.extend(tokens[i + 1 :])
            break
        if not token.startswith("-"):
            pos_args.append(token)
            i += 1
            continue
        opt_name: str
        raw_value: str | None = None
        if token.startswith("--"):
            if "=" in token:
                opt_name, raw_value = token[2:].split("=", 1)
            else:
                opt_name = token[2:]
        else:
            if len(token) == 2:
                opt_name = token[1:]
            else:
                pos_args.append(token)
                i += 1
                continue
        spec = opt_map.get(opt_name) or opt_map.get(f"--{opt_name}") or opt_map.get(f"-{opt_name}")
        if spec is None:
            alt = did_you_mean(
                opt_name, (o.long.lstrip("-") for o in cmd.options if o.long.startswith("--"))
            )
            hint = f" Did you mean --{alt}?" if alt else ""
            raise UsageError(
                f"Unknown option `{token}`.{hint}", hints=["Use --help to see available options."]
            )

        key = spec.long

        if spec.action == OptionAction.STORE_TRUE:
            opts[key] = True
        elif spec.action == OptionAction.STORE_FALSE:
            opts[key] = False
        elif spec.action == OptionAction.COUNT:
            opts[key] = opts.get(key, 0) + 1
        elif spec.action == OptionAction.APPEND:
            if raw_value is not None:
                val = raw_value
            else:
                i += 1
                if i >= len(tokens):
                    raise UsageError(f"Option `{token}` requires a value.")
                val = tokens[i]
            opts.setdefault(key, []).append(val)
        else:
            if raw_value is not None:
                val = raw_value
            else:
                i += 1
                if i >= len(tokens):
                    raise UsageError(f"Option `{token}` requires a value.")
                val = tokens[i]
            if spec.value_type is int:
                try:
                    val = int(val)
                except ValueError:
                    raise UsageError(f"Option `{token}` expects an integer, got `{val}`.")
            elif spec.value_type is float:
                try:
                    val = float(val)
                except ValueError:
                    raise UsageError(f"Option `{token}` expects a number, got `{val}`.")
            if spec.choices and val not in spec.choices:
                raise UsageError(f"Option `{token}` must be one of {spec.choices}, got `{val}`.")
            opts[key] = val
        i += 1

    return opts, pos_args, remainder


def render_help(cmd: Command, console: Console, path: List[str]) -> None:
    full_path = " ".join(path or [cmd.name])

    from rich.panel import Panel

    header = Panel(f"[bold]{full_path}[/] - {cmd.help}", border_style="bright_magenta")
    console.rich.print()
    console.rich.print(header)
    console.rich.print()

    if cmd.description:
        console.info(cmd.description)
        console.rich.print()

    usage = f"  [bold]Usage:[/] [accent]{full_path}[/]"
    if cmd.options:
        usage += " [options]"
    if cmd.subcommands:
        usage += " [muted]<command>[/]"
    if cmd.arguments:
        for arg in cmd.arguments:
            sep = " " if arg.nargs == 1 else " ... "
            usage += f"{sep}[info]{arg.metavar or arg.name.upper()}[/]"
    if cmd.allow_unknown_args:
        usage += " [grey58][-- <passthrough>][/]"
    console.rich.print(usage)
    console.rich.print()

    if cmd.arguments:
        console.info("Arguments")
        for arg in cmd.arguments:
            meta = arg.metavar or arg.name.upper()
            console.rich.print(f"  [info]{meta:<20}[/] {arg.help}")
        console.rich.print()

    if cmd.options:
        console.info("Options")
        for opt in cmd.options:
            label = opt.long
            if opt.short:
                label = f"{opt.short}, {opt.long}"
            metavar = f" [grey58]{opt.metavar}[/]" if opt.metavar else ""
            default = ""
            if opt.default is not None and opt.action == OptionAction.STORE:
                default = f" [default: {opt.default}]"
            console.rich.print(f"  [accent]{label + metavar:<35}[/] {opt.help}{default}")
        console.rich.print()

    if cmd.subcommands:
        console.info("Commands")
        for sub in cmd.subcommands:
            if sub.hidden:
                continue
            console.rich.print(f"  [accent]{sub.name:<20}[/] {sub.help}")
        console.rich.print()

    if cmd.examples:
        console.info("Examples")
        for example in cmd.examples:
            console.rich.print(f"  [grey70]$[/] [accent]{example}[/]")
        console.rich.print()


_global_options = [
    Option("--help", "-h", help="Show this help and exit.", action=OptionAction.STORE_TRUE),
    Option("--version", help="Show version and exit.", action=OptionAction.STORE_TRUE),
    Option("--debug", help="Enable debug output.", action=OptionAction.STORE_TRUE),
    Option("--quiet", "-q", help="Suppress non-essential output.", action=OptionAction.STORE_TRUE),
    Option("--verbose", "-v", help="Increase verbosity (repeatable).", action=OptionAction.COUNT),
]

_GLOBAL_LONG = {o.long for o in _global_options}
_GLOBAL_SHORT = {o.short for o in _global_options if o.short}
_GLOBAL_OPTS_WITH_VALUE = {
    o.long
    for o in _global_options
    if o.action in (OptionAction.STORE, OptionAction.APPEND, OptionAction.COUNT)
}


def _detect_debug(argv: list[str]) -> bool:
    return "--debug" in argv or "-d" in argv


def _strip_global_options(argv: list[str]) -> tuple[list[str], dict[str, bool | str | int]]:
    """Extract global option flags from argv, returning (cleaned_argv, global_opts)."""
    cleaned: list[str] = []
    globals: dict[str, bool | str | int] = {}
    i = 0
    while i < len(argv):
        token = argv[i]
        if token.startswith("--") and "=" in token:
            name, val = token[2:].split("=", 1)
            long_name = f"--{name}"
            if long_name in _GLOBAL_LONG:
                globals[long_name] = val
                i += 1
                continue
        long_match = token if token.startswith("--") else None
        short_match = token if (token.startswith("-") and not token.startswith("--")) else None
        if long_match and long_match in _GLOBAL_LONG:
            globals[long_match] = True
            i += 1
            continue
        if short_match and short_match in _GLOBAL_SHORT:
            globals[short_match] = True
            i += 1
            continue
        cleaned.append(token)
        i += 1
    return cleaned, globals


def main(argv: list[str] | None = None) -> int:
    register_all()
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        console = Console()
        set_console(console)
        return _show_top_help(console)
    if argv[0] == "--version":
        console = Console()
        set_console(console)
        console.rich.print(f"Zoya CLI v{__version__} ({__codename__})")
        return 0
    try:
        return _dispatch(argv)
    except ZoyaError as exc:
        console = get_console()
        console.rich.print(f"[bold red]Error:[/] {exc.message}")
        for hint in exc.hints:
            console.muted(f"  hint: {hint}")
        return exc.exit_code
    except KeyboardInterrupt:
        console = get_console()
        console.print()
        console.muted("Interrupted.")
        return 130
    except Exception as exc:
        console = get_console()
        console.error("An unexpected error occurred.")
        if _detect_debug(argv):
            console.rich.print_exception(show_locals=True)
        else:
            console.muted("  hint: Re-run with --debug to see the full traceback.")
        return 1


def _dispatch(argv: list[str]) -> int:
    clean_argv, global_opts = _strip_global_options(argv)
    debug = global_opts.get("--debug", False) or global_opts.get("-d", False)
    config = Config(
        project_path=(find_project_root() or Path.cwd()) / "zoya.toml"
        if find_project_root()
        else None
    )
    console = Console(config=config)
    set_console(console)

    cmd, remaining = _walk_tree(clean_argv)

    if not cmd.options:
        cmd_copy = Command(
            name=cmd.name,
            help=cmd.help,
            description=cmd.description,
            options=list(cmd.options),
            arguments=list(cmd.arguments),
            subcommands=list(cmd.subcommands),
            examples=list(cmd.examples),
            run=cmd.run,
            allow_unknown_args=cmd.allow_unknown_args,
            hidden=cmd.hidden,
            plugin=cmd.plugin,
        )
        cmd = cmd_copy
    existing_long = {o.long for o in cmd.options}
    for go in _global_options:
        if go.long not in existing_long:
            cmd.options.append(go)

    opts, pos_args, remainder = _parse_options(cmd, remaining, debug=debug)
    opts.update(global_opts)

    if opts.get("--help") or opts.get("-h"):
        path = _resolve_path(cmd, argv)
        render_help(cmd, console, path)
        return 0

    if not cmd.is_leaf() and cmd.subcommands:
        if not pos_args:
            path = _resolve_path(cmd, argv)
            render_help(cmd, console, path)
            return 0
        raise CommandNotFoundError(
            command=pos_args[0], suggestions=suggest(pos_args[0], (s.name for s in cmd.subcommands))
        )

    if not cmd.is_leaf():
        path = _resolve_path(cmd, argv)
        render_help(cmd, console, path)
        return 0

    min_args = sum(a.nargs for a in cmd.arguments if a.nargs > 0)
    if len(pos_args) < min_args:
        cmd_name = " ".join(_resolve_path(cmd, argv))
        raise UsageError(
            f"Command `{cmd_name}` requires at least {min_args} positional argument(s), "
            f"got {len(pos_args)}.",
            hints=[
                f"Usage: {cmd_name} {' '.join(a.metavar or a.name.upper() for a in cmd.arguments)}"
            ],
        )

    project_root = find_project_root()
    ctx = Context(
        opts=opts,
        args=pos_args,
        command_path=_resolve_path(cmd, argv),
        console=console,
        ui=None,
        config=config,
        project_root=project_root,
        debug=debug,
        remainder=remainder,
    )

    result = cmd.run(ctx)
    return 0 if result is None else result


def _resolve_path(cmd: Command, argv: list[str]) -> list[str]:
    path: list[str] = [registry.root.name]
    node = registry.root
    for token in argv:
        sub = node.get_subcommand(token)
        if sub is not None:
            path.append(token)
            node = sub
            if sub is cmd:
                break
        else:
            break
    return path


def _show_top_help(console: Console) -> int:
    from rich.panel import Panel

    console.rich.print()
    console.banner("Zoya CLI", f"v{__version__} ({__codename__})")
    console.rich.print()
    console.rich.print(
        Panel("The all-in-one developer tool for Python projects.", border_style="bright_magenta")
    )
    console.rich.print()
    console.info("Usage:  [accent]zoya[/] [muted]<command>[/] [options]")
    console.rich.print()
    console.info("Commands")
    for cmd in registry.top_level():
        console.rich.print(f"  [accent]{cmd.name:<20}[/] {cmd.help}")
    console.rich.print()
    console.info("Global Options")
    for opt in _global_options:
        label = opt.long
        if opt.short:
            label = f"{opt.short}, {opt.long}"
        console.rich.print(f"  [accent]{label:<25}[/] {opt.help}")
    console.rich.print()
    console.info("Learn more")
    console.muted("  Use '[accent]zoya <command> --help[/]' for detailed command help.")
    console.rich.print()
    return 0


def entrypoint() -> None:
    sys.exit(main())
