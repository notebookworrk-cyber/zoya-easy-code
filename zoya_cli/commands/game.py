"""Game command group: zoya game new / run / build / export / assets / physics."""

from __future__ import annotations

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from zoya_cli.commands.base import Command, Context, Argument, Option, OptionAction
from zoya_cli.core.registry import register
from zoya_cli.core.errors import GameError, ProjectError, EnvironmentError_


_DEFAULT_GAME_TPL = textwrap.dedent("""\
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill((0, 0, 0))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
""")

_PHYSICS_TPL = textwrap.dedent("""\
    import math

    GRAVITY = 9.81

    class PhysicsObject:
        def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, mass=1.0):
            self.x = x
            self.y = y
            self.vx = vx
            self.vy = vy
            self.mass = mass

        def update(self, dt: float):
            self.vy += GRAVITY * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
""")


def _check_pygame() -> None:
    if not shutil.which("pygame") and not shutil.which("pygame-ce"):
        raise EnvironmentError_(
            "Pygame is not installed. Games require pygame or pygame-ce.",
            hints=["Install with: pip install pygame-ce"],
        )


def _cmd_game_new(ctx: Context) -> int:
    name = ctx.args[0] if ctx.args else "my-game"
    root = Path.cwd() / name
    if root.exists():
        raise GameError(f"Directory `{name}` already exists.")
    root.mkdir(parents=True)
    (root / "main.py").write_text(_DEFAULT_GAME_TPL, encoding="utf-8")
    (root / "assets").mkdir()
    (root / "assets" / ".gitkeep").write_text("")
    (root / "zoya.toml").write_text(
        f'[project]\nname = "{name}"\ntemplate = "game"\n', encoding="utf-8"
    )
    ctx.console.success(f"Created game `{name}`.")
    ctx.console.info("  cd {name} && zoya game run")
    return 0


def _cmd_game_run(ctx: Context) -> int:
    _check_pygame()
    root = Path.cwd()
    main = root / "main.py"
    if not main.exists():
        raise GameError("No main.py found in the project. Use `zoya game new <name>`.")
    ctx.console.info("Starting game...")
    result = subprocess.run([sys.executable, str(main)], cwd=root)
    return result.returncode


def _cmd_game_build(ctx: Context) -> int:
    root = Path.cwd()
    dest = root / "dist"
    dest.mkdir(exist_ok=True)
    for f in root.iterdir():
        if f.is_file() and f.suffix in (".py", ".toml", ".png", ".jpg", ".wav", ".ogg"):
            shutil.copy2(f, dest / f.name)
    for dirname in ("assets",):
        src = root / dirname
        if src.is_dir():
            shutil.copytree(src, dest / dirname, dirs_exist_ok=True)
    ctx.console.success(f"Game build complete → {dest}")
    return 0


def _cmd_game_export(ctx: Context) -> int:
    _check_pygame()
    ctx.console.info("Exporting game to standalone executable...")
    root = Path.cwd()
    main = root / "main.py"
    if not main.exists():
        raise GameError("No main.py found.")
    if not shutil.which("pyinstaller"):
        ctx.console.warn("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--onefile", "--windowed", str(main)], cwd=root
    )
    if result.returncode != 0:
        raise GameError("Export failed.")
    ctx.console.success("Game exported to dist/")
    return 0


def _cmd_game_assets(ctx: Context) -> int:
    root = Path.cwd()
    assets_dir = root / "assets"
    if not assets_dir.is_dir():
        ctx.console.warn("No assets/ directory found. Creating one...")
        assets_dir.mkdir(parents=True)
        (assets_dir / ".gitkeep").write_text("")
    items = sorted(assets_dir.iterdir()) if assets_dir.exists() else []
    if not items:
        ctx.console.info("assets/ directory is empty.")
        return 0
    ctx.console.info("Assets")
    for item in items:
        ctx.console.muted(f"  {item.name} ({item.stat().st_size} bytes)")
    return 0


def _cmd_game_physics(ctx: Context) -> int:
    root = Path.cwd()
    phys_file = root / "physics.py"
    if not phys_file.exists():
        phys_file.write_text(_PHYSICS_TPL, encoding="utf-8")
        ctx.console.success("Created physics.py with a basic physics template.")
    else:
        ctx.console.info(phys_file.read_text(encoding="utf-8"))
    return 0


def register_game_commands() -> None:
    game_group = Command(
        "game",
        help="Game development commands",
        description="Create, run, build, export, and manage game projects.",
        examples=["zoya game new my-rpg", "zoya game run", "zoya game export"],
    )
    game_group.add_command(
        Command(
            "new",
            help="Create a new game project",
            arguments=[Argument("name", "Game project name")],
            run=_cmd_game_new,
        )
    )
    game_group.add_command(Command("run", help="Run the game", run=_cmd_game_run))
    game_group.add_command(
        Command("build", help="Build the game distribution", run=_cmd_game_build)
    )
    game_group.add_command(
        Command("export", help="Export game to standalone executable", run=_cmd_game_export)
    )
    game_group.add_command(Command("assets", help="List game assets", run=_cmd_game_assets))
    game_group.add_command(
        Command("physics", help="Create or view a physics template", run=_cmd_game_physics)
    )
    register(game_group)
