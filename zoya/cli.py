from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from . import run
from .repl import main as repl_main
from .tools.docs import run as docs_run
from .version import __version__


def run_file(filepath: str) -> None:
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
        run(source, filepath)
    except FileNotFoundError:
        print(f"Error: file not found '{filepath}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> NoReturn:
    if len(sys.argv) > 1 and sys.argv[1] == "docs":
        docs_run(sys.argv[2:])
        sys.exit(0)

    parser = argparse.ArgumentParser(
        prog="zoya",
        description="Zoya - A beginner-friendly programming language for AI, automation, and game development",
        epilog="Examples:\n  zoya script.zoya\n  zoya docs file.zoya\n  zoya --repl\n  zoya --version",
    )

    parser.add_argument(
        "file",
        nargs="?",
        help="Zoya source file to execute (.zoya)",
    )

    parser.add_argument(
        "-r",
        "--repl",
        action="store_true",
        help="Start interactive REPL session",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show version information and exit",
    )

    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show example programs and exit",
    )

    parser.add_argument(
        "-c",
        "--command",
        dest="inline_cmd",
        type=str,
        help="Execute a one-liner Zoya command",
    )

    args = parser.parse_args()

    if args.version:
        print(f"Zoya v{__version__}")
        print(
            "A beginner-friendly programming language for AI, automation, and game development"
        )
        sys.exit(0)

    if args.examples:
        show_examples()
        sys.exit(0)

    if args.inline_cmd:
        try:
            run(args.inline_cmd)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if args.repl:
        repl_main()
        sys.exit(0)

    if args.file:
        run_file(args.file)
        sys.exit(0)

    parser.print_help()
    print(
        "\nTry: zoya --help\n  or: zoya --examples\n  or: zoya --repl\n  or: zoya docs <file.zoya>"
    )
    sys.exit(1)


def show_examples() -> None:
    examples = """
Zoya Examples
=============

Hello World:
    print "Hello, World!"

Variables & Math:
    x = 10
    y = 20
    print "Sum: " + (x + y)

Functions:
    fn greet(name) {
        return "Hello, " + name
    }
    print greet("World")

If/Else:
    age = 18
    if age >= 18 {
        print "Adult"
    } else {
        print "Child"
    }

While Loop:
    x = 0
    while x < 5 {
        print x
        x = x + 1
    }

Loop:
    loop 3 {
        print "Hello"
    }

Lists:
    nums = [1, 2, 3]
    nums.append(4)
    print nums[0]

Dictionaries:
    person = {"name": "Alice", "age": 30}
    print person["name"]

String Interpolation:
    name = "Zoya"
    print f"Hello, {name}!"
"""
    print(examples)


if __name__ == "__main__":
    main()
