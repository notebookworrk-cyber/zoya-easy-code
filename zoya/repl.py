"""Read-eval-print loop for interactive Zoya sessions."""

from __future__ import annotations

import os
import sys

from . import run


class ZoyaREPL:
    def __init__(self) -> None:
        self.history_file = os.path.expanduser("~/.zoya_history")
        self.history: list[str] = []
        self._load_history()

    def _load_history(self) -> None:
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, encoding="utf-8") as f:
                    self.history = [line.rstrip("\n") for line in f.readlines() if line.strip()]
        except OSError:
            self.history = []

    def _save_history(self) -> None:
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                for line in self.history[-100:]:
                    f.write(line + "\n")
        except OSError:
            pass

    def _show_banner(self) -> None:
        banner = """
+------------------------------------+
| Zoya Interactive REPL v1.0         |
| Type :help for commands             |
| Type :quit or Ctrl+C to exit       |
+------------------------------------+
"""
        print(banner)

    def _show_help(self) -> None:
        help_text = """
REPL Commands
=============
:help       - Show this help message
:clear      - Clear the screen
:history    - Show command history
:save       - Save history to file
:quit / :q  - Exit the REPL
:examples   - Show example programs

Zoya Syntax Quick Reference
===========================
print "Hello"              - Print text
x = 10                     - Variable assignment
if x > 5 { ... }           - Conditionals
while x < 5 { ... }        - While loop
loop 3 { ... }             - Repeat loop
fn name() { ... }          - Function definition
return value               - Return from function
import "module"            - Import module
[1, 2, 3]                  - List literal
{"key": "val"}             - Dict literal
f"Hello {name}"            - String interpolation
"""
        print(help_text)

    def _show_history(self) -> None:
        if not self.history:
            print("(no history)")
            return
        print("\n--- Command History ---")
        for i, cmd in enumerate(self.history[-30:], 1):
            print(f"{i:3}. {cmd}")
        print()

    def _run_line(self, line: str) -> bool:
        try:
            run(line)
            return True
        except SystemExit:
            raise
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    def run(self) -> None:
        self._show_banner()

        while True:
            try:
                line = input("zoya> ").strip()
            except KeyboardInterrupt:
                print("\nUse :quit to exit")
                continue
            except EOFError:
                print("\nGoodbye!")
                break

            if not line:
                continue

            if line == ":quit" or line == ":q":
                print("Goodbye!")
                break

            if line == ":help":
                self._show_help()
                continue

            if line == ":clear":
                os.system("cls" if os.name == "nt" else "clear")
                self._show_banner()
                continue

            if line == ":history":
                self._show_history()
                continue

            if line == ":save":
                self._save_history()
                print("History saved")
                continue

            if line == ":examples":
                from .cli import show_examples

                show_examples()
                continue

            self.history.append(line)
            self._run_line(line)

        self._save_history()


def main() -> None:
    repl = ZoyaREPL()
    repl.run()
