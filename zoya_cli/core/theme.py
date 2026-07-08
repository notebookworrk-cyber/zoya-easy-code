"""Theme registry for the Zoya CLI.

A theme is a named palette mapped onto Rich style strings. Themes are
user-selectable via ``zoya config set theme <name>`` and influence the accent
colors used across panels, progress bars and banners.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class Theme:
    name: str
    #: Accent color used for headers, banners and emphasis.
    accent: str
    #: Secondary color used for subtitles and muted text.
    muted: str
    #: Color for success states.
    success: str
    #: Color for warnings.
    warning: str
    #: Color for errors.
    error: str
    #: Color for progress bars.
    progress: str
    #: Color for tables / structure.
    info: str
    #: Optional description shown in ``zoya config`` / docs.
    description: str = ""


THEMES: Dict[str, Theme] = {
    "aurora": Theme(
        "aurora",
        accent="bright_magenta",
        muted="dim grey70",
        success="green",
        warning="yellow",
        error="red",
        progress="magenta",
        info="cyan",
        description="Default vibrant theme.",
    ),
    "ocean": Theme(
        "ocean",
        accent="bright_cyan",
        muted="dim grey58",
        success="spring_green1",
        warning="gold1",
        error="red",
        progress="cyan",
        info="dodger_blue1",
        description="Calm blue palette.",
    ),
    "mono": Theme(
        "mono",
        accent="white",
        muted="grey58",
        success="bright_white",
        warning="bright_white",
        error="bright_white",
        progress="white",
        info="bright_white",
        description="High-contrast monochrome theme.",
    ),
    "solar": Theme(
        "solar",
        accent="bright_yellow",
        muted="grey66",
        success="green",
        warning="bright_yellow",
        error="bright_red",
        progress="yellow",
        info="orange1",
        description="Warm solarized-inspired palette.",
    ),
}

DEFAULT_THEME = "aurora"


def get_theme(name: str | None) -> Theme:
    """Return a theme by name, falling back to the default."""
    if not name:
        return THEMES[DEFAULT_THEME]
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def theme_names() -> list[str]:
    return list(THEMES)
