"""Zoya CLI - a world-class developer tool."""

from __future__ import annotations

from zoya_cli._meta import __version__, __codename__
from zoya_cli.cli import main, entrypoint


__all__ = ["__version__", "__codename__", "main", "entrypoint"]
