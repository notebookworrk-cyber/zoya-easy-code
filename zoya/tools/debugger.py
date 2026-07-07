"""Interactive debugger utilities for inspecting and tracing Zoya code execution."""

from __future__ import annotations

import sys
from typing import Any

from zoya.ast import ASTNode, Block, Function
from zoya.interpreter import Interpreter, ZoyaFunction
from zoya.lexer import tokenize
from zoya.parser import parse


class DebugInterpreter(Interpreter):
    def __init__(
        self, source_lines: list[str], file: str = "", breakpoints: set[int] | None = None
    ) -> None:
        super().__init__(file)
        self.source_lines = source_lines
        self.breakpoints = breakpoints or set()
        self._stepping = True
        self._done = False
        self._call_stack: list[str] = []

    def _eval_block(self, block: ASTNode) -> Any:
        if isinstance(block, Block):
            result = None
            for stmt in block.statements:
                if self._done:
                    break
                if self._should_pause(stmt):
                    self._debug_prompt(stmt)
                result = self._eval(stmt)
                if self._done:
                    break
            return result
        return self._eval(block)

    def _should_pause(self, stmt: ASTNode) -> bool:
        line = getattr(stmt, "line", 0)
        if self._stepping:
            return True
        if line in self.breakpoints:
            self._stepping = True
            return True
        return False

    def _debug_prompt(self, stmt: ASTNode) -> None:
        line = getattr(stmt, "line", 0)
        self._show_context(line)
        while not self._done:
            try:
                cmd = input("(zoya-dbg) ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                self._done = True
                return

            if not cmd:
                cmd = "step"

            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if action in ("s", "step"):
                self._stepping = True
                return
            if action in ("c", "continue"):
                self._stepping = False
                return
            if action in ("q", "quit", "exit"):
                self._done = True
                return
            if action in ("p", "print"):
                self._do_print(arg)
            if action in ("b", "break"):
                self._do_break(arg)
            if action in ("v", "vars"):
                self._show_vars()
            if action == "stack":
                self._show_stack()
            if action == "help":
                self._show_help()

    def _show_context(self, line: int) -> None:
        start = max(0, line - 2)
        end = min(len(self.source_lines), line + 1)
        print()

        if self._call_stack:
            print(f"  Call stack: {' -> '.join(self._call_stack)}")

        for i in range(start, end):
            prefix = "->" if i + 1 == line else "  "
            print(f"  {prefix} {i + 1:4d} | {self.source_lines[i].rstrip()}")

        print(f"  [Breakpoints: {sorted(self.breakpoints)}]")
        print()

    def _do_print(self, arg: str) -> None:
        if not arg:
            print("  Usage: print <variable>")
            return
        try:
            val = self.current_env.get(arg)
            print(f"  {arg} = {val!r}")
        except Exception:
            print(f"  '{arg}' is not defined")

    def _do_break(self, arg: str) -> None:
        if not arg:
            print("  Usage: break <line_number>")
            return
        try:
            ln = int(arg)
            if ln in self.breakpoints:
                self.breakpoints.discard(ln)
                print(f"  Removed breakpoint at line {ln}")
            else:
                self.breakpoints.add(ln)
                print(f"  Set breakpoint at line {ln}")
        except ValueError:
            print(f"  Invalid line number: {arg}")

    def _show_vars(self) -> None:
        if hasattr(self.current_env, "_vars"):
            print("  Variables:")
            for name, val in sorted(self.current_env._vars.items()):
                if not name.startswith("_"):
                    print(f"    {name} = {val!r}")
        else:
            print("  (no variables)")

    def _show_stack(self) -> None:
        if self._call_stack:
            print("  Call stack:")
            for frame in reversed(self._call_stack):
                print(f"    {frame}")
        else:
            print("  (module level)")

    @staticmethod
    def _show_help() -> None:
        print("""
  Debug Commands:
    s, step      - Execute next statement
    c, continue  - Continue until next breakpoint
    p, print <v> - Print variable value
    b, break <l> - Toggle breakpoint at line
    v, vars      - Show all variables
    stack        - Show call stack
    q, quit      - Exit debugger
    help         - Show this help
""")

    def _eval(self, node: ASTNode) -> Any:
        if isinstance(node, Function):
            old = self._call_stack[:]
            self._call_stack.append(node.name)
            try:
                return super()._eval(node)
            finally:
                self._call_stack = old
        return super()._eval(node)

    def _call_function(self, call):
        callee = self._eval(call.callee)
        if isinstance(callee, ZoyaFunction):
            self._call_stack.append(callee.name)
            try:
                return super()._call_function(call)
            finally:
                self._call_stack.pop()
        return super()._call_function(call)


def debug(source: str, filepath: str = "") -> None:
    lines = source.split("\n")
    breakpoints: set[int] = set()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("#"):
            if "break" in stripped.lower():
                breakpoints.add(i)
                lines[i - 1] = ""

    source = "\n".join(lines)

    try:
        tokens = tokenize(source, filepath)
        ast = parse(tokens, filepath)
    except Exception as e:
        print(f"Error parsing source: {e}", file=sys.stderr)
        return

    interpreter = DebugInterpreter(lines, filepath, breakpoints)

    print("Zoya Debugger v2.0")
    print("Type 'help' for commands, 'quit' to exit")
    print(f"Breakpoints set at lines: {sorted(breakpoints)}")

    try:
        interpreter._eval_block(ast)
    except SystemExit:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

    print("\nDebugger finished.")
