"""Export package for converting Zoya data to various output formats."""

__version__ = "0.1.0"

import json
import os
import textwrap
from enum import Enum
from typing import Any

__all__ = [
    "ExportTarget",
    "ExportConfig",
    "Exporter",
    "ExportResult",
    "ExportError",
    "generate_dockerfile",
    "generate_setup_py",
    "generate_html_wrapper",
    "generate_requirements",
]


class ExportError(Exception):
    pass


class ExportTarget(str, Enum):
    WEB = "web"
    DESKTOP = "desktop"
    MOBILE = "mobile"
    CLI = "cli"
    LIBRARY = "library"
    DOCKER = "docker"


class ExportConfig:
    def __init__(
        self,
        target: ExportTarget,
        output_dir: str,
        minify: bool = False,
        include_tests: bool = False,
        include_docs: bool = False,
        entry_point: str = "main.zy",
        format: str = "source",
    ) -> None:
        self.target = target
        self.output_dir = output_dir
        self.minify = minify
        self.include_tests = include_tests
        self.include_docs = include_docs
        self.entry_point = entry_point
        self.format = format


class ExportResult:
    def __init__(
        self,
        success: bool,
        files: dict[str, str] | None = None,
        output_dir: str = "",
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
        target: ExportTarget | None = None,
    ) -> None:
        self.success = success
        self.files = files or {}
        self.output_dir = output_dir
        self.errors = errors or []
        self.warnings = warnings or []
        self.target = target or ExportTarget.WEB


def generate_requirements(source: str) -> str:
    reqs: dict[str, str] = {"zoya": ">=0.1.0"}
    lines = [
        f"{pkg}>={ver}" if ver.startswith(">=") else f"{pkg}{ver}" for pkg, ver in reqs.items()
    ]
    if "import flask" in source or "from flask" in source:
        lines.append("flask>=3.0.0")
    if "import django" in source or "from django" in source:
        lines.append("django>=5.0.0")
    if "import requests" in source:
        lines.append("requests>=2.31.0")
    return "\n".join(lines) + "\n"


def generate_dockerfile(source: str) -> str:
    return textwrap.dedent("""\
    FROM python:3.12-slim

    WORKDIR /app

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . .

    EXPOSE 8080

    CMD ["python", "main.py"]
    """)


def generate_setup_py(source: str) -> str:
    name = "zoya-app"
    version = "0.1.0"
    for line in source.splitlines():
        line = line.strip()
        if line.startswith("# name:"):
            name = line.split(":")[1].strip()
        if line.startswith("# version:"):
            version = line.split(":")[1].strip()
    return textwrap.dedent(f"""\
    from setuptools import setup, find_packages

    setup(
        name="{name}",
        version="{version}",
        packages=find_packages(),
        install_requires={json.dumps(generate_requirements(source).splitlines())},
        entry_points={{
            "console_scripts": [
                "{name}=main:main",
            ],
        }},
    )
    """)


def generate_html_wrapper(code: str) -> str:
    escaped = (
        code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )
    return textwrap.dedent(f"""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zoya App</title>
    <script src="https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js"></script>
    </head>
    <body>
    <div id="app"></div>
    <script>
    async function main() {{
        const pyodide = await loadPyodide();
        const code = `{escaped}`;
        await pyodide.runPythonAsync(code);
    }}
    main();
    </script>
    </body>
    </html>
    """)


class Exporter:
    def export(self, source: str, config: ExportConfig) -> ExportResult:
        method_map: dict[ExportTarget, Any] = {
            ExportTarget.WEB: self.export_web,
            ExportTarget.DESKTOP: self.export_desktop,
            ExportTarget.MOBILE: self.export_mobile,
            ExportTarget.CLI: self.export_cli,
            ExportTarget.LIBRARY: self.export_library,
            ExportTarget.DOCKER: self.export_docker,
        }
        exporter = method_map.get(config.target)
        if exporter is None:
            raise ExportError(f"Unsupported export target: {config.target}")
        return exporter(source, config)

    def export_web(self, source: str, config: ExportConfig) -> ExportResult:
        files: dict[str, str] = {}
        name = os.path.splitext(config.entry_point)[0]
        files[f"{name}.html"] = generate_html_wrapper(source)
        files[config.entry_point] = source
        files["requirements.txt"] = generate_requirements(source)
        if config.include_tests:
            files["tests/test_app.py"] = self._generate_test_stub(source)
        result = ExportResult(
            success=True, files=files, output_dir=config.output_dir, target=ExportTarget.WEB
        )
        return result

    def export_desktop(self, source: str, config: ExportConfig) -> ExportResult:
        files: dict[str, str] = {}
        name = os.path.splitext(config.entry_point)[0]
        files[f"{name}.py"] = source
        files["run.py"] = textwrap.dedent(f"""\
        import sys
        import {name}

        def main():
            app = {name}.create_app()
            app.run()

        if __name__ == "__main__":
            main()
        """)
        files["requirements.txt"] = generate_requirements(source)
        if config.include_tests:
            files["tests/test_app.py"] = self._generate_test_stub(source)
        result = ExportResult(
            success=True, files=files, output_dir=config.output_dir, target=ExportTarget.DESKTOP
        )
        return result

    def export_mobile(self, source: str, config: ExportConfig) -> ExportResult:
        files: dict[str, str] = {}
        os.path.splitext(config.entry_point)[0]
        files["app/__init__.py"] = "# Zoya Mobile App\n"
        files["app/main.py"] = source
        files["app/main_view.py"] = textwrap.dedent("""\
        from zoya.ui import View, Label, Button, VStack

        class MainView(View):
            def __init__(self):
                super().__init__()
                self.title = "Zoya App"

            def body(self):
                return VStack(
                    Label("Hello from Zoya Mobile"),
                    Button("Tap me", on_click=self.on_tap),
                )

            def on_tap(self):
                print("Tapped!")
        """)
        files["requirements.txt"] = generate_requirements(source)
        if config.include_tests:
            files["tests/test_mobile.py"] = self._generate_test_stub(source)
        result = ExportResult(
            success=True, files=files, output_dir=config.output_dir, target=ExportTarget.MOBILE
        )
        return result

    def export_cli(self, source: str, config: ExportConfig) -> ExportResult:
        files: dict[str, str] = {}
        name = os.path.splitext(config.entry_point)[0]
        files[f"{name}.py"] = source
        shebang = "#!/usr/bin/env python3\n\n"
        main_block = textwrap.dedent(f"""\
        import sys
        import {name}

        def main():
            result = {name}.cli_main(sys.argv[1:])
            print(result)

        if __name__ == "__main__":
            main()
        """)
        files[f"{name}_cli.py"] = shebang + main_block
        files["requirements.txt"] = generate_requirements(source)
        if config.include_tests:
            files["tests/test_cli.py"] = self._generate_test_stub(source)
        result = ExportResult(
            success=True, files=files, output_dir=config.output_dir, target=ExportTarget.CLI
        )
        return result

    def export_library(self, source: str, config: ExportConfig) -> ExportResult:
        files: dict[str, str] = {}
        name = os.path.splitext(config.entry_point)[0]
        lib_dir = name.replace("-", "_")
        files[f"{lib_dir}/__init__.py"] = source
        files["setup.py"] = generate_setup_py(source)
        files["requirements.txt"] = generate_requirements(source)
        if config.include_tests:
            files["tests/test_library.py"] = self._generate_test_stub(source)
        if config.include_docs:
            files["README.md"] = f"# {name}\n\nZoya library package.\n"
        result = ExportResult(
            success=True, files=files, output_dir=config.output_dir, target=ExportTarget.LIBRARY
        )
        return result

    def export_docker(self, source: str, config: ExportConfig) -> ExportResult:
        files: dict[str, str] = {}
        name = os.path.splitext(config.entry_point)[0]
        files[f"{name}.py"] = source
        files["Dockerfile"] = generate_dockerfile(source)
        files["requirements.txt"] = generate_requirements(source)
        files["docker-compose.yml"] = textwrap.dedent("""\
        version: "3.9"
        services:
          app:
            build: .
            ports:
              - "8080:8080"
            volumes:
              - .:/app
            environment:
              - PYTHONUNBUFFERED=1
        """)
        files[".dockerignore"] = textwrap.dedent("""\
        __pycache__
        *.pyc
        .env
        .git
        .venv
        """)
        if config.include_tests:
            files["tests/test_docker.py"] = self._generate_test_stub(source)
        result = ExportResult(
            success=True, files=files, output_dir=config.output_dir, target=ExportTarget.DOCKER
        )
        return result

    def _generate_test_stub(self, source: str) -> str:
        return textwrap.dedent("""\
        import pytest

        def test_import():
            try:
                import app
                assert True
            except ImportError:
                assert False, "Failed to import app"
        """)
