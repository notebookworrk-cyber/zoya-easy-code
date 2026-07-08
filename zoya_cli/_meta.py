"""Zoya CLI - version metadata.

The single source of truth for the CLI version. Kept dependency-free so that
``import zoya_cli._meta`` is instantaneous (important for fast startup).
"""

from __future__ import annotations

__version__ = "5.0.0"
__codename__ = "Aurora"

# Minimum supported Python interpreter.
PYTHON_REQUIRES = "3.11"

# The Zoya language/runtime version this CLI drives.
RUNTIME_VERSION = "4.0.0"
