"""Terminal UI helpers: progress, spinners, prompts, status.

Wraps Rich's progress/status APIs into simple, memorable functions used by
command implementations.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable, Generator, Iterable, Iterator, TypeVar

from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
    TaskID,
)
from rich.status import Status
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.console import Console as RichConsole

from zoya_cli.term.console import Console, get_console

T = TypeVar("T")

# Default progress instance (lazy-initialized)
_progress: Progress | None = None


def _get_progress() -> Progress:
    global _progress
    if _progress is None:
        c = get_console()
        _progress = Progress(
            SpinnerColumn(style=c._styles["progress"]),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style=c._styles["progress"]),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=c.rich,
            transient=True,
        )
    return _progress


# -------------------------------- progress
@contextmanager
def progress_bar() -> Generator[Progress, None, None]:
    """Context manager yielding a Rich Progress instance."""
    prog = _get_progress()
    prog.start()
    try:
        yield prog
    finally:
        prog.stop()


def track(
    iterable: Iterable[T], description: str = "Processing...", total: int | None = None
) -> Iterator[T]:
    """Yield items from *iterable* while displaying a progress bar."""
    prog = _get_progress()
    prog.start()
    task = prog.add_task(
        description, total=total or len(iterable) if hasattr(iterable, "__len__") else None
    )
    try:
        for item in iterable:
            yield item
            prog.advance(task)
    finally:
        prog.stop()
        prog.remove_task(task)


def add_task(description: str, total: int | None = None) -> TaskID:
    """Add a task to the global progress bar (call within ``progress_bar``)."""
    return _get_progress().add_task(description, total=total)


def advance(task: TaskID, n: int = 1) -> None:
    _get_progress().advance(task, n)


def update_task(task: TaskID, **fields: Any) -> None:
    _get_progress().update(task, **fields)


# -------------------------------- spinners / status
@contextmanager
def spinner(message: str = "Working...") -> Generator[Status, None, None]:
    """Context manager yielding a Rich Status spinner."""
    c = get_console()
    with c.rich.status(message, spinner="dots", spinner_style=c._styles["progress"]) as status:
        yield status


def spin(message: str) -> Status:
    """Return a started Status spinner (call .stop() when done)."""
    c = get_console()
    status = c.rich.status(message, spinner="dots", spinner_style=c._styles["progress"])
    status.start()
    return status


# -------------------------------- prompts
def prompt(message: str, default: str | None = None, password: bool = False) -> str:
    c = get_console()
    return Prompt.ask(message, default=default, password=password, console=c.rich)


def confirm(message: str, default: bool = True) -> bool:
    c = get_console()
    return Confirm.ask(message, default=default, console=c.rich)


def int_prompt(message: str, default: int | None = None) -> int:
    c = get_console()
    return IntPrompt.ask(message, default=default, console=c.rich)


def float_prompt(message: str, default: float | None = None) -> float:
    c = get_console()
    return FloatPrompt.ask(message, default=default, console=c.rich)


def select(message: str, choices: list[str], default: str | None = None) -> str:
    """Present a numbered menu and return the chosen item."""
    c = get_console()
    for i, choice in enumerate(choices, 1):
        c.rich.print(f"  {i}. {choice}")
    while True:
        idx = IntPrompt.ask(message, default=1, console=c.rich)
        if 1 <= idx <= len(choices):
            return choices[idx - 1]
        c.warn("Invalid selection, try again.")


def multi_select(message: str, choices: list[str]) -> list[str]:
    """Checkbox-style multi-select via space-separated indices."""
    c = get_console()
    for i, choice in enumerate(choices, 1):
        c.rich.print(f"  {i}. {choice}")
    c.muted("Enter space-separated numbers (e.g. 1 3 4):")
    while True:
        raw = Prompt.ask(message, console=c.rich).strip()
        if not raw:
            return []
        try:
            indices = [int(x) for x in raw.split()]
            if all(1 <= i <= len(choices) for i in indices):
                return [choices[i - 1] for i in indices]
        except ValueError:
            pass
        c.warn("Invalid input, try again.")


# -------------------------------- utilities
def clear() -> None:
    get_console().rich.clear()


def pause(message: str = "Press Enter to continue...") -> None:
    prompt(message, default="")


def print_json(data: Any) -> None:
    import json
    from rich.syntax import Syntax

    c = get_console()
    text = json.dumps(data, indent=2, sort_keys=True)
    c.rich.print(Syntax(text, "json", theme="monokai", word_wrap=True))
