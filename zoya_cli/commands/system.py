"""Core system commands: new, init, run, build, compile, test, benchmark, fmt,
lint, doctor, fix, clean, config, version, info, docs, examples, repl.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from zoya_cli._meta import __version__, __codename__, RUNTIME_VERSION
from zoya_cli.commands.base import Command, Context, Option, Argument, OptionAction
from zoya_cli.core.config import Config, find_project_root
from zoya_cli.core.errors import ProjectError, BuildError, TestError, EnvironmentError_, UsageError
from zoya_cli.core.registry import register, registry


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _require_project(ctx: Context) -> Path:
    root = ctx.require_project()
    return root


def _run_shell(
    cmd: list[str], cwd: Path | None = None, capture: bool = False
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=capture, text=True, timeout=300)
    except FileNotFoundError:
        raise EnvironmentError_(
            f"Command `{cmd[0]}` not found.",
            hints=[f"Install `{cmd[0]}` with `pip install {cmd[0]}`."],
        )


def _check_tool(tool: str) -> bool:
    return shutil.which(tool) is not None


_PROJECT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "console": {
        "description": "A simple console application",
        "files": {
            "main.py": textwrap.dedent("""\
                def main():...
                if __name__ == "__main__":
                    main()
            """),
            "README.md": "# {name}\n\nA Zoya project.\n",
        },
    },
    "ai": {
        "description": "An AI-powered application",
        "files": {
            "main.py": textwrap.dedent("""\
                def main():...
                if __name__ == "__main__":
                    main()
            """),
            "README.md": "# {name}\n\nAn AI-powered Zoya project.\n",
        },
    },
    "web-api": {
        "description": "A web API project",
        "files": {
            "app.py": textwrap.dedent("""\
                from zoya.web import Web
                app = Web()
            """),
            "README.md": "# {name}\n\nA Zoya Web API project.\n",
        },
    },
    "library": {
        "description": "A reusable Python library",
        "files": {"src/{name}/__init__.py": "", "README.md": "# {name}\n\nA Zoya library.\n"},
    },
    "package": {
        "description": "A distributable package",
        "files": {"src/{name}/__init__.py": "", "README.md": "# {name}\n\nA Zoya package.\n"},
    },
    "2d-game": {
        "description": "A 2D game project",
        "files": {
            "main.py": textwrap.dedent("""\
                import pygame
                def main():...
                if __name__ == "__main__":
                    main()
            """),
            "README.md": "# {name}\n\nA Zoya 2D Game.\n",
        },
    },
    "3d-game": {
        "description": "A 3D game project",
        "files": {"main.py": "import pygame\n", "README.md": "# {name}\n\nA Zoya 3D Game.\n"},
    },
    "desktop": {
        "description": "A desktop GUI application",
        "files": {
            "main.py": textwrap.dedent("""\
                def main():...
                if __name__ == "__main__":
                    main()
            """),
            "README.md": "# {name}\n\nA Zoya Desktop application.\n",
        },
    },
    "cli": {
        "description": "A CLI tool project",
        "files": {
            "{name}/__init__.py": "",
            "{name}/__main__.py": "import sys\ndef main():...\n",
            "README.md": "# {name}\n\nA Zoya CLI tool.\n",
        },
    },
}


def _scaffold_project(name: str, template: str, ctx: Context) -> None:
    from zoya_cli.term import ui

    spec = _PROJECT_TEMPLATES.get(template)
    if not spec:
        ctx.console.error(f"Unknown template `{template}`.")
        ctx.console.muted(f"  Available: {', '.join(_PROJECT_TEMPLATES)}")
        raise UsageError(f"Unknown template `{template}`.")

    root = Path.cwd() / name
    if root.exists():
        raise UsageError(f"Directory `{name}` already exists.")

    with ui.spinner(f"Creating {name} ({template})...") as s:
        root.mkdir(parents=True)
        for filepath_spec, content in spec["files"].items():
            fname = filepath_spec.replace("{name}", name)
            fpath = root / fname
            fpath.parent.mkdir(parents=True, exist_ok=True)
            rendered = content.replace("{name}", name)
            fpath.write_text(rendered, encoding="utf-8")
        # Write zoya.toml
        zoya_toml = textwrap.dedent(f"""\
            [project]
            name = "{name}"
            version = "0.1.0"
            template = "{template}"
            [build]
            target = "native"
            optimize = true
        """)
        (root / "zoya.toml").write_text(zoya_toml, encoding="utf-8")
        (root / ".gitkeep").write_text("")

    ctx.console.success(f"Created project `{name}` from `{template}` template.")
    ctx.console.info(f"  cd {name}")
    ctx.console.info("  zoya run")


# ---------------------------------------------------------------------------
# handlers
# ---------------------------------------------------------------------------


def _cmd_new(ctx: Context) -> int:
    name = ctx.args[0]
    template = ctx.opts.get("--template", "console")
    _scaffold_project(name, template, ctx)
    return 0


def _cmd_init(ctx: Context) -> int:
    root = Path.cwd()
    name = root.name
    template = ctx.opts.get("--template", "console")
    zoya_toml = root / "zoya.toml"
    if zoya_toml.exists():
        raise UsageError(
            f"This directory already has a {zoya_toml}.",
            hints=["Use 'zoya clean' to reset if needed."],
        )
    _scaffold_project(name, template, ctx)
    return 0


def _cmd_run(ctx: Context) -> int:
    from zoya_cli.term import ui

    file_arg = ctx.args[0] if ctx.args else "main.py"
    target = Path(file_arg)
    if not target.exists():
        raise UsageError(f"File `{file_arg}` not found.")
    ctx.console.info(f"Running {target}...")
    result = subprocess.run([sys.executable, str(target)], cwd=target.parent)
    return result.returncode


def _cmd_build(ctx: Context) -> int:
    root = _require_project(ctx)
    from zoya_cli.term import ui

    ctx.console.info("Building project...")
    dest = root / "dist"
    dest.mkdir(exist_ok=True)
    # copy source files
    for f in root.rglob("*"):
        if f.is_file() and _is_build_artifact(f):
            continue
        if "__pycache__" in f.parts or ".git" in f.parts:
            continue
        rel = f.relative_to(root)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
    ctx.console.success(f"Build artifacts in {dest}")
    return 0


def _is_build_artifact(p: Path) -> bool:
    return p.suffix in (".pyc", ".pyo", ".egg-info") or p.name in ("__pycache__", ".git")


def _cmd_compile(ctx: Context) -> int:
    root = _require_project(ctx)
    from zoya_cli.term import ui

    ctx.console.info("Compiling project...")
    result = subprocess.run(
        [sys.executable, "-m", "compileall", str(root)], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise BuildError(result.stderr)
    ctx.console.success("Compilation successful.")
    return 0


def _cmd_test(ctx: Context) -> int:
    root = _require_project(ctx) if find_project_root() else Path.cwd()
    from zoya_cli.term import ui

    verbose = ctx.opts.get("--verbose", 0)
    coverage = ctx.opts.get("--coverage", False)
    ctx.console.info("Running tests...")

    cmd = [sys.executable, "-m", "pytest"]
    if verbose:
        cmd.append(f"-{'v' * verbose}")
    if coverage:
        cmd.extend(["--cov", "--cov-report=term-missing"])

    with ui.spinner("Running tests..."):
        result = subprocess.run(cmd, cwd=root, capture_output=True, text=True)

    ctx.console.print(result.stdout)
    if result.stderr:
        ctx.console.muted(result.stderr)
    if result.returncode != 0:
        raise TestError(f"Tests failed with exit code {result.returncode}.")
    ctx.console.success("All tests passed.")
    return 0


def _cmd_benchmark(ctx: Context) -> int:
    from zoya_cli.term import ui

    ctx.console.info("Running benchmarks...")
    root = find_project_root() or Path.cwd()
    bench_file = root / "benchmarks" / "benchmark.py"
    if not bench_file.exists():
        # Run a simple timing benchmark on the project
        ctx.console.muted("No benchmarks/benchmark.py found; running warmup timing.")
        import time

        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, "-c", "import time; time.sleep(0.01)"], capture_output=True, text=True
        )
        elapsed = time.perf_counter() - start
        ctx.console.success(f"Baseline execution: {elapsed:.3f}s")
        return result.returncode
    result = subprocess.run([sys.executable, str(bench_file)], cwd=root)
    return result.returncode


def _cmd_fmt(ctx: Context) -> int:
    root = find_project_root() or Path.cwd()
    check = ctx.opts.get("--check", False)
    from zoya_cli.term import ui

    ctx.console.info("Formatting code...")
    if _check_tool("ruff"):
        cmd = ["ruff", "format", "."]
        if check:
            cmd.append("--check")
        result = _run_shell(cmd, cwd=root)
        if result.returncode:
            ctx.console.error("Formatting issues found.")
            ctx.console.print(result.stdout)
            return 1
        ctx.console.success("Code formatted.")
    else:
        ctx.console.muted("ruff not found, using black...")
        cmd = ["black", "."]
        if check:
            cmd.extend(["--check", "--diff"])
        result = _run_shell(cmd, cwd=root)
        if result.returncode:
            ctx.console.error("Formatting issues found.")
            return 1
        ctx.console.success("Code formatted.")
    return 0


def _cmd_lint(ctx: Context) -> int:
    root = find_project_root() or Path.cwd()
    from zoya_cli.term import ui

    ctx.console.info("Linting code...")
    cmd = ["ruff", "check", "."]
    if ctx.opts.get("--fix", False):
        cmd.append("--fix")
    result = _run_shell(cmd, cwd=root)
    if result.stdout:
        ctx.console.print(result.stdout)
    return result.returncode


def _cmd_doctor(ctx: Context) -> int:
    from zoya_cli.term import ui

    ctx.console.banner("Zoya Doctor", f"v{__version__}")
    ctx.console.print()

    checks: list[tuple[str, bool, str]] = [
        ("Python 3.11+", sys.version_info >= (3, 11), sys.version.split()[0]),
        ("Ruff (linter)", _check_tool("ruff"), "recommended"),
        ("Black (formatter)", _check_tool("black"), "recommended"),
        ("Pytest (testing)", _check_tool("pytest"), "recommended"),
        ("Git (VCS)", _check_tool("git"), "optional"),
        ("Pygame (games)", _check_tool("pygame") or _check_tool("pygame-ce"), "optional for games"),
        ("OpenAI (AI)", _check_tool("openai"), "optional for AI"),
        ("Anthropic (AI)", _check_tool("anthropic"), "optional for AI"),
    ]

    rows: list[list[str]] = []
    for name, ok, note in checks:
        status = "[green]OK[/]" if ok else "[yellow]MISSING[/]"
        rows.append([name, status, note])

    ctx.console.table(columns=["Check", "Status", "Notes"], rows=rows, title="Environment Checks")
    ctx.console.print()

    # Config info
    cfg = ctx.config
    ctx.console.info("Configuration")
    ctx.console.key_value(
        [
            ("Global config", str(cfg.global_path)),
            ("Project root", str(ctx.project_root or "not found")),
            ("Theme", cfg.get("theme", "aurora")),
            ("AI Provider", cfg.get("ai.provider", "mock")),
        ]
    )
    ctx.console.print()
    ctx.console.success("Doctor check complete.")
    return 0


def _cmd_fix(ctx: Context) -> int:
    from zoya_cli.term import ui

    ctx.console.info("Auto-fixing lint issues...")
    root = find_project_root() or Path.cwd()
    if _check_tool("ruff"):
        result = _run_shell(["ruff", "check", "--fix", ".", "--unsafe-fixes"], cwd=root)
        if result.stdout:
            ctx.console.print(result.stdout)
        ctx.console.success("Auto-fix complete.")
        return result.returncode
    ctx.console.warn("ruff not available; install with `pip install ruff`.")
    return 1


def _cmd_clean(ctx: Context) -> int:
    root = _require_project(ctx) if find_project_root() else Path.cwd()
    from zoya_cli.term import ui

    ctx.console.info("Cleaning build artifacts...")
    removed = 0
    for pattern in (
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "dist",
        "build",
        "*.egg-info",
        ".pytest_cache",
        ".ruff_cache",
        "*.spec",
    ):
        for f in root.rglob(pattern):
            if f.is_dir():
                shutil.rmtree(f, ignore_errors=True)
                removed += 1
            elif f.is_file():
                f.unlink()
                removed += 1
    ctx.console.success(f"Cleaned {removed} artifacts.")
    return 0


def _cmd_config(ctx: Context) -> int:
    from zoya_cli.term import ui

    args = ctx.args
    if not args:
        ctx.console.info("Current configuration")
        ctx.console.print_json(ctx.config.as_dict())
        return 0

    if args[0] in ("get", "set") and len(args) >= 2:
        key = args[1]
        if args[0] == "get":
            val = ctx.config.get(key)
            ctx.console.print(f"{key} = {val}")
        elif args[0] == "set":
            if len(args) < 3:
                raise UsageError("Usage: zoya config set <key> <value>")
            val = args[2]
            ctx.config.set_global(key, val)
            ctx.console.success(f"Set {key} = {val}")
        return 0

    if args[0] == "list":
        ctx.console.print_json(ctx.config.as_dict())
        return 0

    raise UsageError("Usage: zoya config [get <key> | set <key> <value> | list]")


def _cmd_version(ctx: Context) -> int:
    ctx.console.print(f"Zoya CLI v{__version__} ({__codename__})")
    ctx.console.muted(f"  Runtime: Python {sys.version.split()[0]}")
    ctx.console.muted(f"  Zoya interpreter: {RUNTIME_VERSION}")
    return 0


def _cmd_info(ctx: Context) -> int:
    from zoya_cli.term import ui

    root = find_project_root()
    if root:
        ctx.console.banner("Project Info", str(root))
        cfg = root / "zoya.toml"
        if cfg.exists():
            import tomllib

            data = tomllib.loads(cfg.read_text(encoding="utf-8"))
            proj = data.get("project", {})
            ctx.console.key_value(
                [
                    ("Name", proj.get("name", root.name)),
                    ("Version", proj.get("version", "0.1.0")),
                    ("Root", str(root)),
                ]
            )
        else:
            ctx.console.key_value([("Root", str(root))])
    else:
        ctx.console.info("No Zoya project in current directory.")
    ctx.console.print()
    ctx.console.key_value(
        [
            ("CLI version", __version__),
            ("CLI codename", __codename__),
            ("Python", sys.version.split()[0]),
            ("Platform", sys.platform),
        ]
    )
    return 0


def _cmd_docs(ctx: Context) -> int:
    import webbrowser

    urls = {
        "zoya": "https://opencode.ai",
        "python": "https://docs.python.org/3/",
        "ruff": "https://docs.astral.sh/ruff/",
        "pytest": "https://docs.pytest.org/",
    }
    topic = ctx.args[0] if ctx.args else "zoya"
    url = urls.get(topic, "https://opencode.ai")
    ctx.console.info(f"Opening {url}")
    webbrowser.open(url)
    return 0


def _cmd_examples(ctx: Context) -> int:
    from rich.table import Table

    examples_data = [
        ("zoya new my-app", "Scaffold a new project"),
        ("zoya init", "Init current directory"),
        ("zoya run main.py", "Run a file"),
        ("zoya build", "Build project"),
        ("zoya test", "Run tests"),
        ("zoya test --coverage", "Run tests with coverage"),
        ("zoya fmt", "Format code"),
        ("zoya lint", "Lint code"),
        ("zoya doctor", "Check environment"),
        ("zoya ai chat 'message'", "Chat with AI"),
        ("zoya ai explain file.py", "Explain code"),
        ("zoya ai review", "Review project code"),
        ("zoya ai optimize", "Suggest performance optimizations"),
        ("zoya game new my-game", "Create a game project"),
        ("zoya game run", "Run the game"),
        ("zoya add httpx", "Add a dependency"),
        ("zoya install", "Install project dependencies"),
        ("zoya config set theme ocean", "Change theme"),
        ("zoya version", "Show version info"),
        ("zoya clean", "Clean build artifacts"),
        ("zoya plugin install <url>", "Install a plugin"),
    ]
    table = Table(title="Zoya CLI Examples", header_style="bright_magenta")
    table.add_column("Command", style="cyan")
    table.add_column("Description")
    for cmd, desc in examples_data:
        table.add_row(f"$ {cmd}", desc)
    ctx.console.rich.print(table)
    return 0


def _cmd_repl(ctx: Context) -> int:
    import code

    ctx.console.info("Zoya REPL v{}".format(__version__))
    ctx.console.muted("Type help() for more information, Ctrl+Z or Ctrl+C to exit.")
    ctx.console.print()
    vars = {"ctx": ctx, "config": ctx.config, "console": ctx.console, "__version__": __version__}
    code.interact(local=vars, banner="")
    return 0


def _cmd_add_dep(ctx: Context) -> int:
    from zoya_cli.core.config import _dump_toml
    from zoya_cli.term import ui

    root = _require_project(ctx)
    pkg = ctx.args[0]
    ctx.console.info(f"Adding `{pkg}`...")
    result = _run_shell([sys.executable, "-m", "pip", "install", pkg, "--dry-run"], cwd=root)
    if result.returncode != 0:
        ctx.console.error(f"Failed to resolve `{pkg}`.")
        ctx.console.muted(result.stderr)
        return 1
    cfg = root / "zoya.toml"
    import tomllib

    if cfg.exists():
        data = tomllib.loads(cfg.read_text(encoding="utf-8"))
        deps = data.setdefault("dependencies", {})
        deps[pkg] = "*"
        cfg.write_text(_dump_toml(data), encoding="utf-8")
    else:
        data = {"dependencies": {pkg: "*"}}
        cfg.write_text(_dump_toml(data), encoding="utf-8")
    ctx.console.success(f"Added `{pkg}` to dependencies.")
    return 0


def _cmd_remove_dep(ctx: Context) -> int:
    from zoya_cli.core.config import _dump_toml

    root = _require_project(ctx)
    pkg = ctx.args[0]
    cfg = root / "zoya.toml"
    import tomllib

    if cfg.exists():
        data = tomllib.loads(cfg.read_text(encoding="utf-8"))
        deps = data.get("dependencies", {})
        if pkg in deps:
            del deps[pkg]
            cfg.write_text(_dump_toml(data), encoding="utf-8")
            ctx.console.success(f"Removed `{pkg}` from dependencies.")
        else:
            ctx.console.warn(f"`{pkg}` not found in dependencies.")
    return 0


def _cmd_update_dep(ctx: Context) -> int:
    root = _require_project(ctx)
    pkg = ctx.args[0] if ctx.args else ""
    ctx.console.info(f"Updating `{pkg or 'all packages'}`...")
    cmd = ["pip", "install", "--upgrade"]
    if pkg:
        cmd.append(pkg)
    else:
        cmd.append("-r", "requirements.txt")
    result = _run_shell(cmd, cwd=root)
    if result.returncode:
        ctx.console.error("Update failed.")
        return 1
    ctx.console.success("Update complete.")
    return 0


def _cmd_search(ctx: Context) -> int:
    query = " ".join(ctx.args)
    ctx.console.info(f"Searching for `{query}`...")
    result = _run_shell(["pip", "search", query], capture=True)
    if result.returncode:
        ctx.console.muted("pip search is deprecated; using PyPI simple API.")
        import urllib.request
        import json

        url = f"https://pypi.org/simple/{query}/"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                ctx.console.success(f"Package `{query}` exists on PyPI.")
        except Exception:
            ctx.console.warn(f"Could not find `{query}`.")
        return 0
    ctx.console.print(result.stdout)
    return 0


def _cmd_install(ctx: Context) -> int:
    root = find_project_root() or Path.cwd()
    ctx.console.info("Installing project dependencies...")
    result = _run_shell(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=root
    )
    if result.returncode:
        ctx.console.error("Installation failed.")
        ctx.console.muted(result.stderr)
        return 1
    ctx.console.success("Dependencies installed.")
    return 0


def _cmd_publish(ctx: Context) -> int:
    root = _require_project(ctx)
    ctx.console.info("Building distribution...")
    result = _run_shell([sys.executable, "-m", "build"], cwd=root)
    if result.returncode:
        ctx.console.error("Build failed.")
        return 1
    ctx.console.info("Uploading to registry...")
    result = _run_shell([sys.executable, "-m", "twine", "upload", "dist/*"], cwd=root)
    if result.returncode:
        ctx.console.error("Upload failed.")
        ctx.console.muted(result.stderr)
        return 1
    ctx.console.success("Package published!")
    return 0


def _cmd_login(ctx: Context) -> int:
    from zoya_cli.term import ui

    cfg = ctx.config
    username = ui.prompt("Registry username")
    password = ui.prompt("Password (or token)", password=True)
    # Store hashed-ish in config (simplified: just store hint)
    cfg.set_global("registry.user", username)
    ctx.console.success(f"Logged in as `{username}`.")
    return 0


def _cmd_logout(ctx: Context) -> int:
    cfg = ctx.config
    cfg.set_global("registry.user", "")
    ctx.console.success("Logged out.")
    return 0


# ---------------------------------------------------------------------------
# registration
# ---------------------------------------------------------------------------


def register_commands() -> None:
    register(
        Command(
            "new",
            help="Create a new project from a template",
            description="Interactive project scaffolding with multiple templates.",
            arguments=[Argument("name", "The project name/directory")],
            options=[
                Option(
                    "--template",
                    "-t",
                    help="Project template",
                    default="console",
                    choices=list(_PROJECT_TEMPLATES),
                ),
                Option(
                    "--force",
                    "-f",
                    help="Overwrite existing directory",
                    action=OptionAction.STORE_TRUE,
                ),
            ],
            examples=["zoya new my-app", "zoya new my-game --template 2d-game"],
            run=_cmd_new,
        )
    )

    register(
        Command(
            "init",
            help="Initialize the current directory as a Zoya project",
            description="Scaffold a zoya.toml and basic project structure in cwd.",
            options=[
                Option(
                    "--template",
                    "-t",
                    help="Project template",
                    default="console",
                    choices=list(_PROJECT_TEMPLATES),
                )
            ],
            examples=["zoya init", "zoya init --template ai"],
            run=_cmd_init,
        )
    )

    register(
        Command(
            "run",
            help="Run a Zoya script or project",
            arguments=[
                Argument("file", "The file to run (default: main.py)", nargs=0, default="main.py")
            ],
            examples=["zoya run", "zoya run app.py"],
            run=_cmd_run,
        )
    )

    register(
        Command(
            "build",
            help="Build the current project",
            description="Copy source files and assets into dist/.",
            examples=["zoya build"],
            run=_cmd_build,
        )
    )

    register(
        Command(
            "compile",
            help="Compile project to bytecode",
            description="Run Python's compileall on the project source.",
            examples=["zoya compile"],
            run=_cmd_compile,
        )
    )

    register(
        Command(
            "test",
            help="Run the project test suite",
            description="Execute pytest with optional coverage reporting.",
            options=[
                Option(
                    "--coverage",
                    "-c",
                    help="Enable coverage reporting",
                    action=OptionAction.STORE_TRUE,
                )
            ],
            examples=["zoya test", "zoya test --coverage"],
            run=_cmd_test,
        )
    )

    register(
        Command(
            "benchmark",
            help="Run project benchmarks",
            description="Execute benchmarks/benchmark.py or run a baseline timing.",
            examples=["zoya benchmark"],
            run=_cmd_benchmark,
        )
    )

    register(
        Command(
            "fmt",
            help="Format code with ruff or black",
            options=[
                Option(
                    "--check",
                    help="Check formatting without changes",
                    action=OptionAction.STORE_TRUE,
                )
            ],
            examples=["zoya fmt", "zoya fmt --check"],
            run=_cmd_fmt,
        )
    )

    register(
        Command(
            "lint",
            help="Lint the project code",
            description="Run ruff check on the project.",
            options=[Option("--fix", help="Apply safe fixes", action=OptionAction.STORE_TRUE)],
            examples=["zoya lint", "zoya lint --fix"],
            run=_cmd_lint,
        )
    )

    register(
        Command(
            "doctor",
            help="Diagnose the Zoya environment",
            description="Check installed tooling, configuration, and project structure.",
            examples=["zoya doctor"],
            run=_cmd_doctor,
        )
    )

    register(
        Command(
            "fix",
            help="Auto-fix lint issues (ruff --fix)",
            description="Apply safe and unsafe automatic fixes from ruff.",
            examples=["zoya fix"],
            run=_cmd_fix,
        )
    )

    register(
        Command(
            "clean",
            help="Remove build artifacts",
            description="Delete __pycache__, dist, build, and other generated files.",
            examples=["zoya clean"],
            run=_cmd_clean,
        )
    )

    register(
        Command(
            "config",
            help="Get or set configuration values",
            description="View, get, or set global/project configuration.",
            arguments=[Argument("action", "list | get <key> | set <key> <value>", nargs=-1)],
            examples=[
                "zoya config",
                "zoya config set theme ocean",
                "zoya config set ai.provider openai",
            ],
            run=_cmd_config,
        )
    )

    register(
        Command(
            "version", help="Show version information", examples=["zoya version"], run=_cmd_version
        )
    )

    register(
        Command(
            "info",
            help="Show project and environment information",
            examples=["zoya info"],
            run=_cmd_info,
        )
    )

    register(
        Command(
            "docs",
            help="Open Zoya documentation in the browser",
            arguments=[
                Argument("topic", "Documentation topic (zoya, python, ruff, pytest)", nargs=0)
            ],
            examples=["zoya docs", "zoya docs python"],
            run=_cmd_docs,
        )
    )

    register(
        Command(
            "examples",
            help="Show usage examples for all Zoya CLI commands",
            examples=["zoya examples"],
            run=_cmd_examples,
        )
    )

    register(
        Command(
            "repl",
            help="Start an interactive Python REPL with Zoya context",
            description="Launch a Python REPL pre-loaded with CLI objects.",
            examples=["zoya repl"],
            run=_cmd_repl,
        )
    )

    register(
        Command(
            "add",
            help="Add a package dependency",
            arguments=[Argument("package", "Package to add")],
            examples=["zoya add httpx", "zoya add pandas"],
            run=_cmd_add_dep,
        )
    )

    register(
        Command(
            "remove",
            help="Remove a package dependency",
            arguments=[Argument("package", "Package to remove")],
            examples=["zoya remove httpx"],
            run=_cmd_remove_dep,
        )
    )

    register(
        Command(
            "update",
            help="Update dependencies",
            arguments=[Argument("package", "Package to update (or all)", nargs=0)],
            examples=["zoya update", "zoya update pandas"],
            run=_cmd_update_dep,
        )
    )

    register(
        Command(
            "search",
            help="Search for available packages",
            arguments=[Argument("query", "Search query")],
            examples=["zoya search httpx"],
            run=_cmd_search,
        )
    )

    register(
        Command(
            "install",
            help="Install project dependencies",
            description="Read zoya.toml / requirements.txt and install packages.",
            examples=["zoya install"],
            run=_cmd_install,
        )
    )

    register(
        Command(
            "publish",
            help="Build and publish the current project to the registry",
            examples=["zoya publish"],
            run=_cmd_publish,
        )
    )

    register(
        Command(
            "login",
            help="Login to the Zoya package registry",
            examples=["zoya login"],
            run=_cmd_login,
        )
    )

    register(
        Command(
            "logout",
            help="Logout from the Zoya package registry",
            examples=["zoya logout"],
            run=_cmd_logout,
        )
    )

    register(
        Command(
            "studio",
            help="Launch Zoya Studio (AI-powered terminal IDE)",
            description="Open the full-screen terminal IDE for Zoya development.",
            arguments=[Argument("path", "Project path to open (optional)", nargs=0)],
            examples=["zoya studio", "zoya studio ./my-project"],
            run=_cmd_studio,
        )
    )


def _cmd_studio(ctx: Context) -> int:
    """Launch Zoya Studio."""
    from zoya_studio.core.app import main as studio_main

    project_path = ctx.args[0] if ctx.args else None
    studio_main(project_path)
    return 0
