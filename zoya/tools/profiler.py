from __future__ import annotations

import time
from typing import Any

from ..ast import ASTNode, Block, Call, Function, Ident
from ..errors import ReturnException
from ..interpreter import Environment, Interpreter, ZoyaFunction
from ..lexer import tokenize
from ..parser import parse


class ProfilingInterpreter(Interpreter):
    def __init__(self, file: str = "") -> None:
        super().__init__(file)
        self.fn_stats: dict[str, dict[str, float | int]] = {}
        self.line_counts: dict[int, int] = {}

    def _eval(self, node: ASTNode) -> Any:
        line = getattr(node, "line", 0)
        if line:
            self.line_counts[line] = self.line_counts.get(line, 0) + 1
        return super()._eval(node)

    def _call_function(self, call: Call) -> Any:
        callee = self._eval(call.callee)

        if isinstance(callee, ZoyaFunction):
            fn_name = callee.name
            args = [self._eval(a) for a in call.args]
            func = callee

            if len(args) != len(func.decl.params):
                from ..errors import RuntimeError_
                raise RuntimeError_(
                    f"Function '{func.decl.name}' expects {len(func.decl.params)} arguments, got {len(args)}",
                    line=call.line, col=call.col, file=self.file,
                )

            func_env = Environment(func.env)
            for param, arg in zip(func.decl.params, args):
                func_env.define(param, arg)

            old_env = self.current_env
            self.current_env = func_env

            start = time.perf_counter()
            try:
                result = self._eval_block(func.decl.body)
            except ReturnException as ret:
                result = ret.value
            elapsed = time.perf_counter() - start

            self.current_env = old_env

            if fn_name not in self.fn_stats:
                self.fn_stats[fn_name] = {"calls": 0, "total_time": 0.0}
            self.fn_stats[fn_name]["calls"] += 1
            self.fn_stats[fn_name]["total_time"] += elapsed

            return result

        return super()._call_function(call)


def profile_source(source: str, filepath: str = "") -> dict:
    tokens = tokenize(source, filepath)
    ast = parse(tokens, filepath)

    interpreter = ProfilingInterpreter(filepath)

    start = time.perf_counter()
    try:
        interpreter._eval_block(ast)
    except Exception:
        pass
    total_time = time.perf_counter() - start

    function_stats: dict[str, dict[str, float | int]] = {}
    for name, stats in interpreter.fn_stats.items():
        c = stats["calls"]
        t = round(stats["total_time"], 6)
        function_stats[name] = {
            "calls": c,
            "total_time": t,
            "avg_time": round(t / c, 6) if c else 0.0,
        }

    return {
        "total_time": round(total_time, 6),
        "function_stats": function_stats,
        "line_counts": dict(sorted(interpreter.line_counts.items())),
    }
