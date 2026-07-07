#!/usr/bin/env python3
"""Zoya CLI — unified command-line interface for all Zoya Easy Code features.

Usage:
    zoya-cli web                      Start a web server
    zoya-cli ai [--prompt "text"]     AI agent interaction
    zoya-cli data load <csv>          Load & inspect a CSV
    zoya-cli data query <csv> "expr"  Filter data
    zoya-cli security hash <text>     Hash text (SHA-256)
    zoya-cli security encrypt <key> <text>  Encrypt text
    zoya-cli security validate email <addr> Validate email
    zoya-cli game list                List available games
    zoya-cli game run <name>          Run a game
    zoya-cli run <file.zoya>          Run a .zoya script
    zoya-cli repl                     Start Zoya REPL
    zoya-cli init <name>              Scaffold a new project
    zoya-cli cloud db <collection>    Cloud database ops
"""

from __future__ import annotations

import argparse
import csv as csv_module
import io
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path


def cmd_web(args: argparse.Namespace) -> None:
    from zoya.web import Web, Request

    app = Web()

    @app.router.route("GET", "/")
    def home(req):
        return {"message": "Zoya Web is running!", "version": "4.0"}

    @app.router.route("GET", "/hello/{name}")
    def greet(req):
        name = req.scope["path"].split("/")[-1]
        return {"greeting": f"Hey {name}!"}

    async def asgi_app(scope, receive, send):
        if scope["type"] != "http":
            return
        req = Request(scope, receive)
        handler = app.router.handle(req.method, req.path, req)
        result = handler(req) if callable(handler) else handler
        body = json.dumps(result if isinstance(result, dict) else {"data": str(result)}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": body})

    import uvicorn

    host = args.host or "127.0.0.1"
    port = args.port or 8080
    print(f"  Zoya Web Server -> http://{host}:{port}")
    uvicorn.run(asgi_app, host=host, port=port)


def cmd_ai(args: argparse.Namespace) -> None:
    from zoya.ai import create_agent

    def mock_llm(prompt, **kw):
        if "hello" in prompt.lower():
            return "Answer: Hey there! I'm Zoya AI."
        if "who" in prompt.lower():
            return "Answer: I'm an AI agent built into the Zoya platform."
        return f"Answer: Mock response to: {prompt[:60]}..."

    agent = create_agent(provider=mock_llm)

    prompt = args.prompt or "hello"
    print(f"  You: {prompt}")
    print(f"  AI:  {agent.run(prompt)}")


def cmd_data(args: argparse.Namespace) -> None:
    from zoya.data import DataFrame, create_dataframe

    if args.action == "load":
        path = args.csv
        if not os.path.exists(path):
            print(f"  Error: file not found '{path}'")
            sys.exit(1)
        df = create_dataframe(path)
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {df.columns}")
        print(df.head(10))

    elif args.action == "query":
        path = args.csv
        expr = args.expr
        if not os.path.exists(path):
            print(f"  Error: file not found '{path}'")
            sys.exit(1)
        df = create_dataframe(path)
        result = df.query(expr)
        print(f"  Query: {expr}")
        print(f"  Results: {len(result)} rows")
        print(result)

    elif args.action == "create":
        import random

        data = {
            "name": ["Alice", "Bob", "Charlie", "Diana"],
            "age": [random.randint(20, 40) for _ in range(4)],
            "score": [random.randint(50, 100) for _ in range(4)],
        }
        df = DataFrame(data)
        print(df)

    else:
        print("  Unknown data action. Use: load, query, create")


def cmd_security(args: argparse.Namespace) -> None:
    from zoya.security import Hasher, AESCipher, Validator

    if args.action == "hash":
        result = Hasher.sha256(args.text)
        print(f"  SHA-256: {result}")

    elif args.action == "encrypt":
        encrypted = AESCipher.encrypt(args.text, args.key)
        decrypted = AESCipher.decrypt(encrypted, args.key)
        print(f"  Encrypted: {encrypted}")
        print(f"  Decrypted: {decrypted}")

    elif args.action == "validate":
        if args.type == "email":
            try:
                Validator.email(args.value)
                print(f"  '{args.value}' is a valid email")
            except Exception as e:
                print(f"  Invalid: {e}")
        elif args.type == "url":
            try:
                Validator.url(args.value)
                print(f"  '{args.value}' is a valid URL")
            except Exception as e:
                print(f"  Invalid: {e}")
        else:
            print("  Unknown validate type. Use: email, url")


def cmd_game(args: argparse.Namespace) -> None:
    games_dir = Path(__file__).parent / "examples"
    games = {
        f.stem: f
        for f in games_dir.glob("*.zoya")
        if f.stem in ("snake", "pong", "platformer", "particles", "3d_cube", "physics_demo")
    }

    if args.action == "list":
        print(f"  Available games ({len(games)}):")
        for name in sorted(games):
            desc = {
                "snake": "Classic Snake game",
                "pong": "2-player Pong",
                "platformer": "Platform runner",
                "particles": "Particle effects demo",
                "3d_cube": "3D cube rendering",
                "physics_demo": "Physics simulation",
            }.get(name, "Zoya game")
            print(f"    - {name}: {desc}")

    elif args.action == "run":
        name = args.name
        if name not in games:
            print(f"  Error: game '{name}' not found. Use 'zoya-cli game list'")
            sys.exit(1)
        print(f"  Starting '{name}'...")
        subprocess.run([sys.executable, "-m", "zoya", str(games[name])], check=False)


def cmd_run(args: argparse.Namespace) -> None:
    if not os.path.exists(args.file):
        print(f"  Error: file not found '{args.file}'")
        sys.exit(1)
    subprocess.run([sys.executable, "-m", "zoya", args.file], check=False)


def cmd_repl(args: argparse.Namespace) -> None:
    subprocess.run([sys.executable, "-m", "zoya", "--repl"], check=False)


def cmd_init(args: argparse.Namespace) -> None:
    name = args.name
    path = Path.cwd() / name
    if path.exists():
        print(f"  Error: '{name}' already exists")
        sys.exit(1)

    path.mkdir(parents=True)
    (path / f"{name}.zoya").write_text(f'print "Hello from {name}!"\n')
    (path / "main.py").write_text(
        textwrap.dedent(f'''\
        """{name} — Zoya project."""
        from zoya.web import Web, Request
        import uvicorn
        import json

        app = Web()

        @app.router.route("GET", "/")
        def home(req):
            return {{"message": "Hello from {name}!"}}

        async def asgi_app(scope, receive, send):
            if scope["type"] != "http":
                return
            req = Request(scope, receive)
            handler = app.router.handle(req.method, req.path, req)
            result = handler(req) if callable(handler) else handler
            body = json.dumps(result).encode()
            await send({{"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]}})
            await send({{"type": "http.response.body", "body": body}})

        if __name__ == "__main__":
            uvicorn.run(asgi_app, host="127.0.0.1", port=8080)
    ''')
    )
    (path / "README.md").write_text(f"# {name}\n\nZoya project.\n")

    print(f"  Created project '{name}' at {path}")
    print(f"    {name}/{name}.zoya")
    print(f"    {name}/main.py")
    print(f"    {name}/README.md")
    print(f"\n  Run:")
    print(f"    cd {name}")
    print(f"    python -m zoya {name}.zoya")
    print(f"    python main.py        # Web server")


def cmd_cloud(args: argparse.Namespace) -> None:
    from zoya.cloud import create_cloud

    cloud = create_cloud()

    if args.action == "db":
        col = args.collection
        if args.db_action == "list":
            print(f"  Listing '{col}'...")
            results = cloud.database.query(col, {})
            for r in results:
                print(f"    {r}")
        elif args.db_action == "add":
            data = json.loads(args.data)
            doc = cloud.database.insert(col, data)
            print(f"  Inserted: {doc}")
        else:
            print("  Unknown db action. Use: list, add")

    elif args.action == "auth":
        email = args.email or "test@zoya.dev"
        pwd = args.password or "password123"
        user = cloud.auth.register(email, pwd, email.split("@")[0])
        print(f"  Registered user: {user.username}")
        session = cloud.auth.login(email, pwd)
        print(f"  Token: {session.token[:20]}...")

    else:
        print("  Unknown cloud action. Use: db, auth")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="zoya-cli",
        description="Zoya Easy Code — unified CLI for all platform features",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              zoya-cli web --port 3000
              zoya-cli ai --prompt "hello"
              zoya-cli data load data.csv
              zoya-cli security hash "my password"
              zoya-cli game run snake
              zoya-cli init my-project
        """),
    )
    parser.add_argument("--version", action="store_true", help="Show version")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # web
    web_parser = subparsers.add_parser("web", help="Start a web server")
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", type=int, default=8080)
    web_parser.set_defaults(func=cmd_web)

    # ai
    ai_parser = subparsers.add_parser("ai", help="AI agent interaction")
    ai_parser.add_argument("--prompt", "-p", default="hello", help="Prompt for the AI")
    ai_parser.set_defaults(func=cmd_ai)

    # data
    data_parser = subparsers.add_parser("data", help="DataFrame operations")
    data_sub = data_parser.add_subparsers(dest="action")
    data_load = data_sub.add_parser("load", help="Load a CSV file")
    data_load.add_argument("csv", help="Path to CSV file")
    data_query = data_sub.add_parser("query", help="Query a CSV file")
    data_query.add_argument("csv", help="Path to CSV file")
    data_query.add_argument("expr", help="Query expression (e.g., 'age > 25')")
    data_sub.add_parser("create", help="Create a sample DataFrame")
    data_parser.set_defaults(func=cmd_data)

    # security
    sec_parser = subparsers.add_parser("security", help="Security tools (hash, encrypt, validate)")
    sec_sub = sec_parser.add_subparsers(dest="action")
    sec_hash = sec_sub.add_parser("hash", help="Hash text with SHA-256")
    sec_hash.add_argument("text", help="Text to hash")
    sec_enc = sec_sub.add_parser("encrypt", help="Encrypt/decrypt text")
    sec_enc.add_argument("key", help="Encryption key")
    sec_enc.add_argument("text", help="Text to encrypt")
    sec_val = sec_sub.add_parser("validate", help="Validate email or URL")
    sec_val.add_argument("type", choices=["email", "url"], help="Type of validation")
    sec_val.add_argument("value", help="Value to validate")
    sec_parser.set_defaults(func=cmd_security)

    # game
    game_parser = subparsers.add_parser("game", help="List and run games")
    game_sub = game_parser.add_subparsers(dest="action")
    game_sub.add_parser("list", help="List available games")
    game_run = game_sub.add_parser("run", help="Run a game")
    game_run.add_argument("name", help="Game name (snake, pong, platformer, etc.)")
    game_parser.set_defaults(func=cmd_game)

    # run
    run_parser = subparsers.add_parser("run", help="Run a .zoya script")
    run_parser.add_argument("file", help="Path to .zoya file")
    run_parser.set_defaults(func=cmd_run)

    # repl
    repl_parser = subparsers.add_parser("repl", help="Start Zoya REPL")
    repl_parser.set_defaults(func=cmd_repl)

    # init
    init_parser = subparsers.add_parser("init", help="Scaffold a new project")
    init_parser.add_argument("name", help="Project name")
    init_parser.set_defaults(func=cmd_init)

    # cloud
    cloud_parser = subparsers.add_parser("cloud", help="Cloud platform operations")
    cloud_sub = cloud_parser.add_subparsers(dest="action")
    cloud_db = cloud_sub.add_parser("db", help="Database operations")
    cloud_db.add_argument("collection", help="Collection name")
    cloud_db.add_argument("db_action", choices=["list", "add"], help="DB operation")
    cloud_db.add_argument("--data", default='{"name": "test"}', help="JSON data for add")
    cloud_auth = cloud_sub.add_parser("auth", help="Auth operations")
    cloud_auth.add_argument("--email", default="test@zoya.dev")
    cloud_auth.add_argument("--password", default="password123")
    cloud_parser.set_defaults(func=cmd_cloud)

    args = parser.parse_args()

    if args.version:
        from zoya.version import __version__

        print(f"Zoya CLI v{__version__}")
        print("Zoya Easy Code — Full-stack Python development platform")
        print("https://github.com/notebookworrk-cyber/zoya-easy-code")
        return

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
