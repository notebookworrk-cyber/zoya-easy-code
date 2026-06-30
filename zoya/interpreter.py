from __future__ import annotations

import os
import sys
from typing import Any, Optional

from .ast import (
    ASTNode,
    Assign,
    AssignAttr,
    AssignIndex,
    BinOp,
    Block,
    Boolean,
    Break,
    Call,
    Continue,
    Dict_,
    Function,
    GetAttr,
    Ident,
    If,
    Import,
    Index,
    Input,
    InterpolatedString,
    List_,
    Loop,
    MethodCall,
    Number,
    Print,
    Return,
    Slice,
    String,
    UnaryOp,
    While,
)
from .builtins import BUILTIN_FUNCTIONS, LIST_METHODS, STRING_METHODS, DICT_METHODS
from .environment import Environment
from .errors import (
    BreakException,
    ContinueException,
    InterpreterError,
    ReturnException,
    RuntimeError_,
)


class ZoyaFunction:
    def __init__(self, decl: Function, env: Environment) -> None:
        self.decl = decl
        self.env = env
        self.name = decl.name

    def __repr__(self) -> str:
        return f"<function {self.name}>"


class ZoyaModule:
    def __init__(self, name: str, functions: dict[str, Any]) -> None:
        self.name = name
        self.__dict__.update(functions)

    def __repr__(self) -> str:
        return f"<module {self.name}>"


class Interpreter:
    def __init__(self, file: str = "") -> None:
        self.global_env = Environment()
        self.current_env = self.global_env
        self.file = file
        self._init_builtins()

    def _init_builtins(self) -> None:
        from .builtins import register_builtins
        register_builtins(self.global_env)

    def interpret(self, node: ASTNode, env: Optional[Environment] = None) -> Any:
        if env is not None:
            self.current_env = env
        return self._eval(node)

    def _eval(self, node: ASTNode) -> Any:
        line = getattr(node, "line", 0)
        col = getattr(node, "col", 0)

        if isinstance(node, Number):
            return node.value

        if isinstance(node, String):
            return node.value

        if isinstance(node, Boolean):
            return node.value

        if isinstance(node, InterpolatedString):
            result = ""
            for part in node.parts:
                if isinstance(part, str):
                    result += part
                elif isinstance(part, tuple):
                    expr_node, fmt = part
                    val = self._eval(expr_node)
                    try:
                        result += format(val, fmt)
                    except (ValueError, TypeError):
                        result += str(val)
                else:
                    val = self._eval(part)
                    result += str(val)
            return result

        if isinstance(node, Ident):
            name = node.name
            if self.current_env.has(name):
                return self.current_env.get(name)
            raise RuntimeError_(
                f"'{name}' is not defined",
                line=line,
                col=col,
                file=self.file,
            )

        if isinstance(node, Assign):
            val = self._eval(node.expr)
            self.current_env.set(node.name, val)
            return val

        if isinstance(node, AssignIndex):
            obj = self._eval(node.obj)
            index = self._eval(node.index)
            val = self._eval(node.expr)
            if isinstance(obj, list) and isinstance(index, int):
                obj[index] = val
            elif isinstance(obj, dict):
                obj[index] = val
            else:
                raise RuntimeError_(
                    "Cannot assign to index of this type",
                    line=line, col=col, file=self.file,
                )
            return val

        if isinstance(node, AssignAttr):
            obj = self._eval(node.obj)
            val = self._eval(node.expr)
            setattr(obj, node.attr, val)
            return val

        if isinstance(node, BinOp):
            op = node.op
            if op == "AND":
                return self._truthy(self._eval(node.left)) and self._truthy(self._eval(node.right))
            if op == "OR":
                return self._truthy(self._eval(node.left)) or self._truthy(self._eval(node.right))

            left = self._eval(node.left)
            right = self._eval(node.right)

            if op == "POW":
                return left ** right
            if op == "MOD":
                return left % right
            if op == "PLUS":
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)
                return left + right
            if op == "MINUS":
                return left - right
            if op == "MUL":
                return left * right
            if op == "DIV":
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return left / right
                raise RuntimeError_(
                    "Division requires numbers",
                    line=line, col=col, file=self.file,
                )
            if op == "GT":
                return left > right
            if op == "LT":
                return left < right
            if op == "EQ":
                return left == right
            if op == "NE":
                return left != right
            if op == "GTE":
                return left >= right
            if op == "LTE":
                return left <= right
            if op == "IN":
                return left in right if hasattr(right, "__contains__") else False
            raise RuntimeError_(
                f"Unknown operator: {op}",
                line=line, col=col, file=self.file,
            )

        if isinstance(node, UnaryOp):
            expr = self._eval(node.expr)
            if node.op == "NOT":
                return not self._truthy(expr)
            if node.op == "MINUS":
                return -expr
            raise RuntimeError_(
                f"Unknown unary operator: {node.op}",
                line=line, col=col, file=self.file,
            )

        if isinstance(node, Print):
            val = self._eval(node.expr)
            print(val)
            return val

        if isinstance(node, Input):
            prompt = ""
            if node.prompt is not None:
                prompt = str(self._eval(node.prompt))
            try:
                return input(prompt)
            except (EOFError, KeyboardInterrupt):
                return ""

        if isinstance(node, Block):
            result = None
            for stmt in node.statements:
                result = self._eval(stmt)
            return result

        if isinstance(node, If):
            cond = self._truthy(self._eval(node.cond))
            if cond:
                return self._eval_block(node.body)
            elif node.else_body is not None:
                return self._eval_block(node.else_body)
            return None

        if isinstance(node, While):
            result = None
            while self._truthy(self._eval(node.cond)):
                try:
                    result = self._eval_block(node.body)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return result

        if isinstance(node, Loop):
            count = self._eval(node.count)
            if not isinstance(count, (int, float)):
                raise RuntimeError_(
                    "Loop count must be a number",
                    line=line, col=col, file=self.file,
                )
            result = None
            for _ in range(int(count)):
                try:
                    result = self._eval_block(node.body)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return result

        if isinstance(node, Break):
            raise BreakException()

        if isinstance(node, Continue):
            raise ContinueException()

        if isinstance(node, Function):
            func = ZoyaFunction(node, self.current_env)
            self.current_env.set(node.name, func)
            return func

        if isinstance(node, Call):
            return self._call_function(node)

        if isinstance(node, GetAttr):
            obj = self._eval(node.obj)
            return getattr(obj, node.attr)

        if isinstance(node, MethodCall):
            return self._call_method(node)

        if isinstance(node, Return):
            val = None
            if node.expr is not None:
                val = self._eval(node.expr)
            raise ReturnException(val)

        if isinstance(node, List_):
            return [self._eval(elem) for elem in node.elements]

        if isinstance(node, Dict_):
            result: dict[Any, Any] = {}
            for key_node, val_node in node.pairs:
                key = self._eval(key_node)
                val = self._eval(val_node)
                result[key] = val
            return result

        if isinstance(node, Index):
            obj = self._eval(node.obj)
            index = self._eval(node.index)
            if isinstance(obj, (list, tuple, str)):
                return obj[int(index)]
            if isinstance(obj, dict):
                return obj[index]
            raise RuntimeError_(
                f"Cannot index {type(obj).__name__}",
                line=line, col=col, file=self.file,
            )

        if isinstance(node, Slice):
            obj = self._eval(node.obj)
            start = self._eval(node.start) if node.start else None
            stop = self._eval(node.stop) if node.stop else None
            step = self._eval(node.step) if node.step else None
            return obj[start:stop:step]

        if isinstance(node, Import):
            return self._handle_import(node)

        raise RuntimeError_(
            f"Unknown AST node: {type(node).__name__}",
            line=line, col=col, file=self.file,
        )

    def _eval_block(self, block: ASTNode) -> Any:
        if isinstance(block, Block):
            result = None
            for stmt in block.statements:
                result = self._eval(stmt)
            return result
        return self._eval(block)

    def _call_function(self, call: Call) -> Any:
        callee = self._eval(call.callee)

        if isinstance(callee, ZoyaModule):
            func_name = call.callee.name if hasattr(call.callee, "name") else ""
            if hasattr(callee, "_call"):
                return callee._call(call.args, self)
            if len(call.args) == 1 and hasattr(callee, call.callee.name if isinstance(call.callee, Ident) else ""):
                ...  # This will be handled below
            raise RuntimeError_(
                f"'{callee.name}' is not callable",
                line=call.line, col=call.col, file=self.file,
            )

        builtin_name = ""
        if isinstance(call.callee, Ident):
            builtin_name = call.callee.name
            if builtin_name in BUILTIN_FUNCTIONS:
                fn = BUILTIN_FUNCTIONS[builtin_name]
                args = [self._eval(arg) for arg in call.args]
                return fn(*args)

        if isinstance(callee, ZoyaFunction):
            args = [self._eval(arg) for arg in call.args]
            func = callee
            if len(args) != len(func.decl.params):
                raise RuntimeError_(
                    f"Function '{func.decl.name}' expects {len(func.decl.params)} arguments, got {len(args)}",
                    line=call.line, col=call.col, file=self.file,
                )
            func_env = Environment(func.env)
            for param, arg in zip(func.decl.params, args):
                func_env.define(param, arg)
            old_env = self.current_env
            self.current_env = func_env
            try:
                return self._eval_block(func.decl.body)
            except ReturnException as ret:
                return ret.value
            finally:
                self.current_env = old_env

        if callable(callee):
            args = [self._eval(arg) for arg in call.args]
            return callee(*args)

        raise RuntimeError_(
            f"'{callee}' is not callable",
            line=call.line, col=call.col, file=self.file,
        )

    def _call_method(self, mc: MethodCall) -> Any:
        obj = self._eval(mc.obj)
        args = [self._eval(arg) for arg in mc.args]
        method = mc.method

        if isinstance(obj, ZoyaModule) and hasattr(obj, method):
            fn = getattr(obj, method)
            if callable(fn):
                return fn(*args)
            return fn

        if isinstance(obj, str) and method in STRING_METHODS:
            return STRING_METHODS[method](obj, *args)

        if isinstance(obj, list) and method in LIST_METHODS:
            return LIST_METHODS[method](obj, *args)

        if isinstance(obj, dict) and method in DICT_METHODS:
            return DICT_METHODS[method](obj, *args)

        if hasattr(obj, method):
            fn = getattr(obj, method)
            if callable(fn):
                return fn(*args)
            return fn

        raise RuntimeError_(
            f"'{type(obj).__name__}' has no method '{method}'",
            line=mc.line, col=mc.col, file=self.file,
        )

    def _handle_import(self, node: Import) -> Any:
        path = node.path
        alias = node.alias or path

        try:
            import importlib
            py_module = importlib.import_module(f"zoya.stdlib.{path}")
            if hasattr(py_module, "load_module"):
                module = py_module.load_module(self)
                self.current_env.set(alias, module)
                return module
        except ImportError:
            pass

        if path in BUILTIN_FUNCTIONS:
            return BUILTIN_FUNCTIONS[path]

        zoya_file = path
        if not zoya_file.endswith(".zoya"):
            zoya_file += ".zoya"

        search_dirs = [
            os.path.dirname(os.path.abspath(self.file)) if self.file else os.getcwd(),
            os.path.join(os.path.dirname(__file__), "stdlib"),
            os.getcwd(),
        ]

        for search_dir in search_dirs:
            full_path = os.path.join(search_dir, zoya_file)
            if os.path.exists(full_path):
                from .lexer import tokenize
                from .parser import parse
                with open(full_path, "r") as f:
                    source = f.read()
                tokens = tokenize(source, full_path)
                ast = parse(tokens, full_path)
                old_file = self.file
                self.file = full_path
                import_env = Environment(self.global_env)
                try:
                    self._eval_block(ast)
                finally:
                    self.file = old_file
                module_obj = ZoyaModule(alias, {})
                for key, val in import_env._vars.items():
                    if not key.startswith("_") and key not in BUILTIN_FUNCTIONS:
                        setattr(module_obj, key, val)
                self.current_env.set(alias, module_obj)
                return module_obj

        raise RuntimeError_(
            f"Module '{path}' not found",
            line=node.line, col=node.col, file=self.file,
        )

    def _truthy(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, (list, dict, tuple)):
            return len(value) > 0
        return bool(value)


def interpret(ast: Block, file: str = "") -> Any:
    interp = Interpreter(file)
    return interp._eval_block(ast)


def run(source: str, file: str = "") -> Any:
    from .lexer import tokenize
    from .parser import parse
    tokens = tokenize(source, file)
    ast = parse(tokens, file)
    return interpret(ast, file)
