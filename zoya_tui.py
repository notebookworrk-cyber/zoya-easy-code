#!/usr/bin/env python3
"""Zoya TUI — Interactive terminal UI for Zoya Easy Code.

Usage:
    python -m zoya_tui
    pip install zoya3 && zoya3
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    ContentSwitcher,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    LoadingIndicator,
    RichLog,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)

WIDTH = 120
HEIGHT = 36


class ZoyaTUI(App):
    TITLE = "Zoya Easy Code"
    SUB_TITLE = "Full-stack Python Development Platform"
    CSS = """
Screen {
    background: #0a0a1a;
}

#menu-grid {
    layout: grid;
    grid-size: 3;
    grid-gutter: 1;
    padding: 1 2;
    height: auto;
}

.menu-btn {
    width: 100%;
    height: 5;
    border: tall $accent;
    background: #1a1a3a;
    color: $text;
    content-align: center middle;
    margin: 0;
}

.menu-btn:hover {
    background: #2a2a5a;
}

.menu-btn > .button-label {
    text-style: bold;
    color: $primary;
}

#header {
    content-align: center middle;
    color: $primary;
    text-style: bold;
}

.back-btn {
    dock: bottom;
    width: 100%;
    height: 3;
}

.section-title {
    text-style: bold;
    color: $primary;
    padding: 0 1;
}

.status-text {
    color: $success;
}

DataTable {
    height: 10;
}

Input {
    margin: 0 1;
}

RichLog {
    border: solid $primary;
    height: 10;
    margin: 1;
}

LoadingIndicator {
    height: 3;
}
"""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield MainMenu()
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        screens = {
            "btn-web": WebScreen,
            "btn-ai": AIScreen,
            "btn-data": DataScreen,
            "btn-security": SecurityScreen,
            "btn-games": GamesScreen,
            "btn-cloud": CloudScreen,
            "btn-repl": REPLScreen,
            "btn-project": ProjectScreen,
            "btn-exit": ExitScreen,
        }
        if btn_id in screens:
            self.push_screen(screens[btn_id]())
        elif event.button.id == "btn-help":
            self.push_screen(HelpScreen())


class MainMenu(Screen):
    def compose(self) -> ComposeResult:
        yield Static("[bold #00ff88]╔══════════════════════════════════════╗[/]", id="hdr-top")
        yield Static("[bold #00ff88]║        ZOYA EASY CODE v4.0           ║[/]", id="hdr-mid")
        yield Static("[bold #00ff88]╚══════════════════════════════════════╝[/]", id="hdr-bot")
        yield Static("")
        with Vertical(id="menu-grid"):
            yield Button(" 1  Web Server  ", id="btn-web", classes="menu-btn")
            yield Button(" 2  AI Chat     ", id="btn-ai", classes="menu-btn")
            yield Button(" 3  Data Explorer", id="btn-data", classes="menu-btn")
            yield Button(" 4  Security    ", id="btn-security", classes="menu-btn")
            yield Button(" 5  Games       ", id="btn-games", classes="menu-btn")
            yield Button(" 6  Cloud       ", id="btn-cloud", classes="menu-btn")
            yield Button(" 7  REPL        ", id="btn-repl", classes="menu-btn")
            yield Button(" 8  New Project ", id="btn-project", classes="menu-btn")
            yield Button(" 9  Help        ", id="btn-help", classes="menu-btn")
            yield Button(" 0  Exit        ", id="btn-exit", classes="menu-btn")

    def on_key(self, event) -> None:
        key_map = {
            "1": "btn-web",
            "2": "btn-ai",
            "3": "btn-data",
            "4": "btn-security",
            "5": "btn-games",
            "6": "btn-cloud",
            "7": "btn-repl",
            "8": "btn-project",
            "9": "btn-help",
            "0": "btn-exit",
            "escape": "btn-exit",
        }
        if event.key in key_map:
            btn = self.query_one(f"#{key_map[event.key]}", Button)
            if btn:
                btn.press()


class BaseScreen(Screen):
    BINDINGS = [Binding("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Static("", id="section-title", classes="section-title")
            yield Static("", id="content-area")
        yield Button("  Back to Menu (ESC)  ", id="back-btn", classes="back-btn")
        yield Footer()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.action_go_back()


class WebScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Static("Web Server", id="section-title", classes="section-title")
            yield Static("Start a Zoya web server with live requests log.")
            with Horizontal():
                yield Input(placeholder="Port (default: 8080)", id="web-port", value="8080")
                yield Button("  Start  ", id="web-start", variant="success")
                yield Button("  Stop   ", id="web-stop", variant="error")
            yield RichLog(id="web-log", highlight=True, markup=True)
            yield Static("Routes:", classes="status-text")
            yield Static("  GET /       → Home")
            yield Static("  GET /hello/{name}  → Greeting")
        yield Button("  Back to Menu (ESC)  ", id="back-btn", classes="back-btn")
        yield Footer()

    _server_proc: subprocess.Popen | None = None

    @on(Button.Pressed, "#web-start")
    def start_web(self) -> None:
        log = self.query_one("#web-log", RichLog)
        port = self.query_one("#web-port", Input).value or "8080"
        log.write(f"[green]Starting web server on port {port}...[/]")
        code = textwrap.dedent(f'''\
import uvicorn, json, sys
sys.path.insert(0, r"{os.getcwd()}")
from zoya.web import Web, Request

app = Web()

@app.router.route("GET", "/")
def home(req):
    return {{"message": "Zoya Web is running!", "version": "4.0"}}

@app.router.route("GET", "/hello/{{name}}")
def greet(req):
    name = req.scope["path"].split("/")[-1]
    return {{"greeting": f"Hey {{name}}!"}}

async def asgi_app(scope, receive, send):
    if scope["type"] != "http":
        return
    req = Request(scope, receive)
    handler = app.router.handle(req.method, req.path, req)
    result = handler(req) if callable(handler) else handler
    body = json.dumps(result).encode()
    await send({{"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]}})
    await send({{"type": "http.response.body", "body": body}})
    print(f"  {{req.method}} {{req.path}} -> 200")

uvicorn.run(asgi_app, host="127.0.0.1", port={port}, log_level="info")
''')
        script_path = Path(__file__).parent / "_web_server.py"
        script_path.write_text(code)
        self._server_proc = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.set_interval(0.5, self._poll_log)

    def _poll_log(self) -> None:
        if self._server_proc and self._server_proc.stdout:
            line = self._server_proc.stdout.readline()
            if line:
                log = self.query_one("#web-log", RichLog)
                log.write(line.rstrip())

    @on(Button.Pressed, "#web-stop")
    def stop_web(self) -> None:
        if self._server_proc:
            self._server_proc.terminate()
            self._server_proc = None
        log = self.query_one("#web-log", RichLog)
        log.write("[red]Server stopped[/]")


class AIScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Static("AI Chat", id="section-title", classes="section-title")
            yield Static("Chat with Zoya's built-in AI agent (no API key needed).")
            yield RichLog(id="ai-log", highlight=True, markup=True)
            with Horizontal():
                yield Input(placeholder="Type your message...", id="ai-input")
                yield Button("  Send  ", id="ai-send", variant="primary")
                yield Button("  Clear  ", id="ai-clear", variant="warning")
        yield Button("  Back to Menu (ESC)  ", id="back-btn", classes="back-btn")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#ai-log", RichLog)
        log.write("[bold cyan]Zoya AI[/] ready! Type a message.")

    @on(Button.Pressed, "#ai-send")
    @on(Input.Submitted, "#ai-input")
    def send_ai(self) -> None:
        inp = self.query_one("#ai-input", Input)
        msg = inp.value.strip()
        if not msg:
            return
        inp.value = ""
        log = self.query_one("#ai-log", RichLog)
        log.write(f"[yellow]You:[/] {msg}")
        self._run_ai(msg)

    @work(thread=True)
    def _run_ai(self, msg: str) -> None:
        def mock_llm(prompt, **kw):
            responses = {
                "hello": "Hey there! I'm Zoya AI, built right into the platform.",
                "who": "I'm Zoya AI — an agent that runs locally with no API keys.",
                "help": "I can chat, answer questions, help with code, and more!",
            }
            for k, v in responses.items():
                if k in msg.lower():
                    return f"Answer: {v}"
            return f'Answer: Got it! You said: "{msg[:80]}". I\'m a mock AI — connect a real LLM provider (OpenAI/Anthropic) for full responses!'

        from zoya.ai import create_agent

        agent = create_agent(provider=mock_llm)
        result = agent.run(msg)
        self.call_from_thread(self._show_ai_result, result)

    def _show_ai_result(self, result: str) -> None:
        log = self.query_one("#ai-log", RichLog)
        log.write(f"[green]AI:[/] {result}")

    @on(Button.Pressed, "#ai-clear")
    def clear_ai(self) -> None:
        self.query_one("#ai-log", RichLog).clear()


class DataScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Static("Data Explorer", id="section-title", classes="section-title")
            with Horizontal():
                yield Button("  Create Sample  ", id="data-sample", variant="primary")
                yield Button("  Load CSV  ", id="data-load", variant="success")
            yield Input(placeholder="CSV file path...", id="data-path")
            yield Input(placeholder="Query (e.g., age > 25)", id="data-query")
            yield Button("  Run Query  ", id="data-query-btn", variant="warning")
            yield DataTable(id="data-table")
        yield Button("  Back to Menu (ESC)  ", id="back-btn", classes="back-btn")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#data-table", DataTable)
        table.add_columns("name", "age", "score")

    @on(Button.Pressed, "#data-sample")
    def create_sample(self) -> None:
        import random
        from zoya.data import DataFrame

        data = DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
                "age": [random.randint(20, 40) for _ in range(5)],
                "score": [random.randint(50, 100) for _ in range(5)],
            }
        )
        self._show_df(data)

    @on(Button.Pressed, "#data-load")
    def load_csv(self) -> None:
        path = self.query_one("#data-path", Input).value
        if not path or not os.path.exists(path):
            self.query_one("#data-table", DataTable).clear()
            return
        from zoya.data import create_dataframe

        df = create_dataframe(path)
        self._show_df(df)

    @on(Button.Pressed, "#data-query-btn")
    def run_query(self) -> None:
        path = self.query_one("#data-path", Input).value
        expr = self.query_one("#data-query", Input).value
        if not path or not expr:
            return
        from zoya.data import create_dataframe

        try:
            df = create_dataframe(path)
            result = df.query(expr)
            self._show_df(result)
        except Exception as e:
            self.query_one("#data-table", DataTable).clear().add_column("Error")
            self.query_one("#data-table", DataTable).add_row(str(e))

    def _show_df(self, df) -> None:
        table = self.query_one("#data-table", DataTable)
        table.clear()
        table.add_columns(*df.columns)
        for _, row in df.iterrows():
            values = [str(getattr(row, c, "")) for c in df.columns]
            table.add_row(*values)


class SecurityScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Static("Security Tools", id="section-title", classes="section-title")
            with Horizontal():
                yield Button("  SHA-256  ", id="sec-hash", variant="primary")
                yield Button("  Encrypt  ", id="sec-encrypt", variant="success")
                yield Button("  Validate Email  ", id="sec-email", variant="warning")
            yield Input(placeholder="Input text...", id="sec-input")
            yield Input(placeholder="Encryption key (for encrypt)", id="sec-key")
            yield RichLog(id="sec-log", highlight=True, markup=True)
        yield Button("  Back to Menu (ESC)  ", id="back-btn", classes="back-btn")
        yield Footer()

    @on(Button.Pressed, "#sec-hash")
    def do_hash(self) -> None:
        from zoya.security import Hasher

        text = self.query_one("#sec-input", Input).value or "hello"
        result = Hasher.sha256(text)
        log = self.query_one("#sec-log", RichLog)
        log.write(f"[bold]SHA-256([/]{text}[bold]):[/]")
        log.write(f"[green]{result}[/]")

    @on(Button.Pressed, "#sec-encrypt")
    def do_encrypt(self) -> None:
        from zoya.security import AESCipher

        text = self.query_one("#sec-input", Input).value or "secret"
        key = self.query_one("#sec-key", Input).value or "default-key"
        encrypted = AESCipher.encrypt(text, key)
        decrypted = AESCipher.decrypt(encrypted, key)
        log = self.query_one("#sec-log", RichLog)
        log.write(f"[bold]Original:[/] {text}")
        log.write(f"[yellow]Encrypted:[/] {encrypted}")
        log.write(f"[green]Decrypted:[/] {decrypted}")

    @on(Button.Pressed, "#sec-email")
    def do_email(self) -> None:
        from zoya.security import Validator

        email = self.query_one("#sec-input", Input).value or "test@example.com"
        try:
            Validator.email(email)
            self.query_one("#sec-log", RichLog).write(f"[green]'{email}' is valid[/]")
        except Exception as e:
            self.query_one("#sec-log", RichLog).write(f"[red]Invalid: {e}[/]")


class GamesScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Static("Games", id="section-title", classes="section-title")
            yield Static("Browse and launch Zoya games (requires pygame-ce).")
            yield ListView(id="game-list")
        yield Button("  Back to Menu (ESC)  ", id="back-btn", classes="back-btn")
        yield Footer()

    def on_mount(self) -> None:
        games_dir = Path(__file__).parent / "examples"
        game_list = self.query_one("#game-list", ListView)
        game_names = ["snake", "pong", "platformer", "particles", "3d_cube", "physics_demo"]
        for name in game_names:
            path = games_dir / f"{name}.zoya"
            desc = {
                "snake": "Classic Snake",
                "pong": "2-Player Pong",
                "platformer": "Platform Runner",
                "particles": "Particle Demo",
                "3d_cube": "3D Cube",
                "physics_demo": "Physics",
            }
            if path.exists():
                game_list.append(ListItem(Static(f"  {name:15}  {desc.get(name, '')}")))

    @on(ListView.Selected, "#game-list")
    def launch_game(self, event: ListView.Selected) -> None:
        item_text = str(event.item.children[0].renderable).strip()
        name = item_text.split()[0]
        game_path = Path(__file__).parent / "examples" / f"{name}.zoya"
        self.app.push_screen(ConfirmScreen(f"Launch '{name}'?", "game", str(game_path)))


class CloudScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Static("Cloud Platform", id="section-title", classes="section-title")
            yield Button("  Auth (register + login)  ", id="cloud-auth", variant="primary")
            yield Button("  DB: List users  ", id="cloud-db", variant="success")
            yield RichLog(id="cloud-log", highlight=True, markup=True)
        yield Button("  Back to Menu (ESC)  ", id="back-btn", classes="back-btn")
        yield Footer()

    @on(Button.Pressed, "#cloud-auth")
    def do_auth(self) -> None:
        from zoya.cloud import create_cloud

        cloud = create_cloud()
        log = self.query_one("#cloud-log", RichLog)
        try:
            user = cloud.auth.register("demo@zoya.dev", "pass123", "demo")
            log.write(f"[green]Registered:[/] {user.username} ({user.email})")
            session = cloud.auth.login("demo@zoya.dev", "pass123")
            log.write(f"[green]Logged in:[/] token={session.token[:16]}...")
        except Exception as e:
            log.write(f"[yellow]{e}[/]")
            session = cloud.auth.login("demo@zoya.dev", "pass123")
            log.write(f"[green]Logged in:[/] token={session.token[:16]}...")

    @on(Button.Pressed, "#cloud-db")
    def do_db(self) -> None:
        from zoya.cloud import create_cloud

        cloud = create_cloud()
        log = self.query_one("#cloud-log", RichLog)
        cloud.database.insert("users", {"name": "Alice", "email": "alice@test.com"})
        cloud.database.insert("users", {"name": "Bob", "email": "bob@test.com"})
        results = cloud.database.query("users", {})
        log.write(f"[bold]Users in DB ({len(results)}):[/]")
        for r in results:
            log.write(f"  {r}")


class REPLScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Static("Zoya REPL", id="section-title", classes="section-title")
            yield Static("Write Zoya code and see output below.")
            yield TextArea(id="repl-code", language="python")
            with Horizontal():
                yield Button("  Run  ", id="repl-run", variant="primary")
                yield Button("  Clear  ", id="repl-clear", variant="warning")
            yield RichLog(id="repl-log", highlight=True, markup=True)
        yield Button("  Back to Menu (ESC)  ", id="back-btn", classes="back-btn")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(
            "#repl-code", TextArea
        ).text = 'print "Hello Zoya!"\nx = 42\nprint "Answer: " + x'

    @on(Button.Pressed, "#repl-run")
    def run_repl(self) -> None:
        code = self.query_one("#repl-code", TextArea).text
        log = self.query_one("#repl-log", RichLog)
        log.write(f"[yellow]> {code.split(chr(10))[0]}...[/]")
        self._run_code(code)

    @work(thread=True)
    def _run_code(self, code: str) -> None:
        import io, contextlib
        from zoya import run

        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                run(code)
            output = buf.getvalue()
        except Exception as e:
            output = f"Error: {e}"
        self.call_from_thread(self._show_output, output)

    def _show_output(self, output: str) -> None:
        log = self.query_one("#repl-log", RichLog)
        for line in output.strip().split("\n"):
            log.write(f"[green]{line}[/]")

    @on(Button.Pressed, "#repl-clear")
    def clear_repl(self) -> None:
        self.query_one("#repl-log", RichLog).clear()
        self.query_one("#repl-code", TextArea).text = ""


class ProjectScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Static("New Project", id="section-title", classes="section-title")
            yield Static("Scaffold a new Zoya project with web server.")
            yield Input(placeholder="Project name...", id="proj-name")
            yield Button("  Create  ", id="proj-create", variant="primary")
            yield RichLog(id="proj-log", highlight=True, markup=True)
        yield Button("  Back to Menu (ESC)  ", id="back-btn", classes="back-btn")
        yield Footer()

    @on(Button.Pressed, "#proj-create")
    def create_project(self) -> None:
        name = self.query_one("#proj-name", Input).value.strip()
        if not name:
            return
        log = self.query_one("#proj-log", RichLog)
        path = Path.cwd() / name
        if path.exists():
            log.write(f"[red]Error: '{name}' already exists[/]")
            return
        path.mkdir(parents=True)
        (path / f"{name}.zoya").write_text(f'print "Hello from {name}!"\n')
        (path / "main.py").write_text(f'print("Hello from {name}!")\n')
        (path / "README.md").write_text(f"# {name}\n\nA Zoya project.\n")
        log.write(f"[green]Created project '{name}' at {path}[/]")
        log.write(f"  cd {name}")
        log.write(f"  python -m zoya {name}.zoya")
        self.query_one("#proj-name", Input).value = ""


class ConfirmScreen(ModalScreen):
    def __init__(self, question: str, action: str, target: str = "") -> None:
        super().__init__()
        self._question = question
        self._action = action
        self._target = target

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Static(self._question)
            with Horizontal():
                yield Button("  Yes  ", id="confirm-yes", variant="success")
                yield Button("  No   ", id="confirm-no", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-yes" and self._action == "game":
            subprocess.Popen(
                [sys.executable, "-m", "zoya", self._target],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        self.app.pop_screen()


class HelpScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Static("Help", id="section-title", classes="section-title")
            yield Static("""
Zoya Easy Code v4.0 — Full-stack Python development platform

  [bold]Web Server[/]     Start a local web API server
  [bold]AI Chat[/]        Talk to Zoya's built-in AI agent
  [bold]Data Explorer[/]  Load/query CSV data as DataFrames
  [bold]Security[/]       Hash, encrypt, validate emails
  [bold]Games[/]          Launch Snake, Pong, Platformer, etc.
  [bold]Cloud[/]          In-memory auth & database demo
  [bold]REPL[/]           Write and run Zoya code interactively
  [bold]New Project[/]    Scaffold a starter project

[bold]Key bindings:[/]
  ESC / 0      Back/Exit
  1-9          Menu shortcuts
  Tab/Shift+Tab  Navigate

[bold]Install as command:[/]
  pip install zoya3
  zoya3

[bold]Links:[/]
  GitHub: https://github.com/notebookworrk-cyber/zoya-easy-code
            """)
        yield Button("  Back to Menu (ESC)  ", id="back-btn", classes="back-btn")
        yield Footer()


class ExitScreen(ModalScreen):
    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Static("Exit Zoya?")
            with Horizontal():
                yield Button("  Yes  ", id="exit-yes", variant="error")
                yield Button("  No   ", id="exit-no", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit-yes":
            self.app.exit()
        else:
            self.app.pop_screen()


import textwrap


def main() -> None:
    app = ZoyaTUI()
    app.run()


if __name__ == "__main__":
    main()
