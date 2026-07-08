"""Rich console wrapper for the Zoya CLI.

Provides a single configured :class:`rich.console.Console` instance with
theme-aware styles, consistent output handling, and helpers for banners,
panels, and structured output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.align import Align
from rich.style import Style

from zoya_cli.core.theme import get_theme, Theme
from zoya_cli.core.config import Config


class Console:
    """Theme-aware console with convenience methods for common CLI patterns."""

    def __init__(self, config: Config | None = None, theme_name: str | None = None) -> None:
        self._config = config
        self._theme: Theme = get_theme(theme_name or (config.get("theme") if config else None))
        self._rich = RichConsole(color_system="auto")
        self._styles = self._build_styles()

    def _build_styles(self) -> dict[str, Style]:
        t = self._theme
        return {
            "accent": Style.parse(t.accent),
            "muted": Style.parse(t.muted),
            "success": Style.parse(t.success),
            "warning": Style.parse(t.warning),
            "error": Style.parse(t.error),
            "progress": Style.parse(t.progress),
            "info": Style.parse(t.info),
        }

    @property
    def theme(self) -> Theme:
        return self._theme

    @property
    def rich(self) -> RichConsole:
        return self._rich

    # ---------------------------- basic output delegation
    def print(self, *args: Any, **kwargs: Any) -> None:
        self._rich.print(*args, **kwargs)

    def log(self, *args: Any, **kwargs: Any) -> None:
        self._rich.log(*args, **kwargs)

    def rule(self, title: str = "", style: str = "muted") -> None:
        self._rich.rule(title, style=self._styles.get(style, "muted"))

    # ---------------------------- styled helpers
    def banner(self, title: str, subtitle: str = "") -> None:
        """Print a full-width banner with accent styling."""
        text = Text(title, style=self._styles["accent"].bold)
        if subtitle:
            text.append(" ")
            text.append(subtitle, style=self._styles["muted"])
        self._rich.print(Align.center(text))

    def panel(self, content: str, title: str = "", border_style: str = "accent", **kwargs) -> None:
        """Print a Rich panel with theme-aware border."""
        panel = Panel(
            content, title=title, border_style=self._styles.get(border_style, "accent"), **kwargs
        )
        self._rich.print(panel)

    def info(self, message: str) -> None:
        self._rich.print(message, style=self._styles["info"])

    def success(self, message: str) -> None:
        self._rich.print(message, style=self._styles["success"].bold)

    def warn(self, message: str) -> None:
        self._rich.print(message, style=self._styles["warning"].bold)

    def error(self, message: str) -> None:
        self._rich.print(message, style=self._styles["error"].bold)

    def muted(self, message: str) -> None:
        self._rich.print(message, style=self._styles["muted"])

    # ---------------------------- structured output
    def table(
        self, columns: list[str], rows: list[list[Any]], title: str = "", show_header: bool = True
    ) -> None:
        """Print a formatted table."""
        table = Table(title=title, show_header=show_header, header_style=self._styles["accent"])
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*[str(c) for c in row])
        self._rich.print(table)

    def tree(self, label: str, children: dict[str, Any], style: str = "accent") -> None:
        """Print a tree view."""
        tree = Tree(label, style=self._styles.get(style, "accent"))
        self._add_tree_nodes(tree, children)
        self._rich.print(tree)

    def _add_tree_nodes(self, node: Tree, data: dict[str, Any]) -> None:
        for key, value in data.items():
            if isinstance(value, dict):
                branch = node.add(key, style=self._styles["muted"])
                self._add_tree_nodes(branch, value)
            elif isinstance(value, (list, tuple)):
                branch = node.add(key, style=self._styles["muted"])
                for i, item in enumerate(value):
                    branch.add(f"[{i}] {item}")
            else:
                node.add(f"{key}: {value}")

    def key_value(self, pairs: list[tuple[str, Any]], indent: int = 2) -> None:
        """Print aligned key-value pairs."""
        pad = " " * indent
        for k, v in pairs:
            self._rich.print(f"{pad}[{self._styles['accent']}]{k}[/]: {v}")

    def print_error(self, exc: BaseException, debug: bool = False) -> None:
        """Pretty-print any exception."""
        self.error(str(exc))
        if debug:
            import traceback

            self._rich.print_exception(show_locals=True)


# Global singleton (lazy-initialized by CLI entrypoint)
_console: Console | None = None


def get_console(config: Config | None = None) -> Console:
    global _console
    if _console is None:
        _console = Console(config)
    return _console


def set_console(console: Console) -> None:
    global _console
    _console = console
