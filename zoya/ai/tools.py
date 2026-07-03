"""Tool Registry and Built-in Tools for the Zoya AI Platform.

Provides an abstract Tool base class, a ToolRegistry for managing tools,
and a set of built-in tools including calculator, web search, file I/O,
Python execution, and shell commands.
"""

from typing import List, Dict, Any, Optional, Callable
from abc import ABC, abstractmethod
import math
import json
import re
import ast
import os
import threading
import io


class ToolError(Exception):
    """Base exception for tool operations."""
    pass


class Tool(ABC):
    """Abstract base class for tools that can be used by LLM providers.

    Each tool has a name, description, JSON schema for parameters,
    and an execute method that performs the tool's function.
    """

    def __init__(
        self,
        name: str = "",
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.name = name or getattr(self.__class__, "name", self.__class__.__name__)
        self.description = description or getattr(self.__class__, "description", "")
        self.parameters = parameters or getattr(self.__class__, "parameters", {})

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        ...

    def to_openai_format(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def to_anthropic_format(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


class ToolRegistry:
    """Registry for managing and accessing tools.

    Provides registration, lookup, execution, and serialization of tools
    to provider-specific formats (OpenAI, Anthropic).
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ToolError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise ToolError(
                f"Tool '{name}' not found. "
                f"Available tools: {list(self._tools.keys())}"
            )
        return self._tools[name]

    def list(self) -> List[Tool]:
        return list(self._tools.values())

    def execute(self, name: str, **kwargs) -> Any:
        return self.get(name).execute(**kwargs)

    def to_openai_tools(self) -> List[Dict[str, Any]]:
        return [tool.to_openai_format() for tool in self._tools.values()]

    def to_anthropic_tools(self) -> List[Dict[str, Any]]:
        return [tool.to_anthropic_format() for tool in self._tools.values()]


def tool(name: str = None, description: str = None):
    """Decorator that converts a function into a Tool.

    The function's signature and docstring are used to auto-generate
    the tool's name, description, and parameter JSON schema.

    Args:
        name: Optional override for the tool name (defaults to function name).
        description: Optional override for the tool description (defaults to
            function docstring).

    Returns:
        A Tool instance wrapping the decorated function.
    """
    def decorator(func: Callable) -> Tool:
        import inspect
        sig = inspect.signature(func)
        parameters: Dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            type(None): "null",
        }
        for param_name, param in sig.parameters.items():
            param_type = "string"
            if param.annotation is not inspect.Parameter.empty:
                origin = getattr(param.annotation, "__origin__", None)
                if origin is list:
                    param_type = "array"
                elif origin is dict:
                    param_type = "object"
                else:
                    base = param.annotation
                    if isinstance(base, type):
                        param_type = type_map.get(base, "string")
            parameters["properties"][param_name] = {"type": param_type}
            if param.default is inspect.Parameter.empty:
                parameters["required"].append(param_name)

        tool_name = name or func.__name__
        tool_desc = description or (func.__doc__ or "").strip()

        class _FunctionTool(Tool):
            def __init__(self):
                super().__init__(
                    name=tool_name,
                    description=tool_desc,
                    parameters=parameters,
                )

            def execute(self, **kwargs) -> Any:
                return func(**kwargs)

        return _FunctionTool()
    return decorator


#
# ─── Built-in Tools ───────────────────────────────────────────────────
#


class Calculator(Tool):
    """Evaluate math expressions safely using eval with restricted globals."""

    name = "calculator"
    description = (
        "Evaluate a mathematical expression and return the numeric result. "
        "Supports all functions from Python's math module."
    )
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": (
                    "The mathematical expression to evaluate. "
                    "Examples: '2 + 2', 'sin(pi/4)', 'sqrt(16)', "
                    "'log(100, 10)', '3 * 4 + 2'"
                ),
            }
        },
        "required": ["expression"],
    }

    def __init__(self):
        super().__init__()

    def execute(self, expression: str) -> str:
        try:
            tree = ast.parse(expression.strip(), mode="eval")
            allowed_types = {
                ast.Expression, ast.BinOp, ast.UnaryOp,
                ast.Add, ast.Sub, ast.Mult, ast.Div,
                ast.FloorDiv, ast.Mod, ast.Pow,
                ast.USub, ast.UAdd,
                ast.Constant, ast.Call, ast.Name, ast.Load,
            }
            for node in ast.walk(tree):
                if type(node) not in allowed_types:
                    raise ToolError(
                        f"Expression contains disallowed element: "
                        f"{type(node).__name__}"
                    )
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id not in dir(math):
                            raise ToolError(
                                f"Function '{node.func.id}' is not allowed. "
                                f"Only math module functions are available."
                            )

            safe_globals: Dict[str, Any] = {"__builtins__": {}}
            safe_globals.update(
                (name, getattr(math, name))
                for name in dir(math)
                if not name.startswith("_")
            )

            result = eval(compile(tree, "<string>", "eval"), safe_globals)
            return json.dumps({"result": result})
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Calculator evaluation failed: {e}")


class WebSearchTool(Tool):
    """Search the web for information.

    Returns mock results by default. A real search function can be
    injected via the constructor for production use.
    """

    name = "web_search"
    description = (
        "Search the web for information. "
        "Returns a list of relevant results with titles, URLs, and snippets."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string",
            },
        },
        "required": ["query"],
    }

    def __init__(self, search_func: Optional[Callable[[str], Any]] = None):
        super().__init__()
        self._search_func = search_func

    def execute(self, query: str) -> str:
        if self._search_func is not None:
            try:
                result = self._search_func(query)
                return json.dumps(result)
            except Exception as e:
                raise ToolError(f"Web search failed: {e}")
        return json.dumps({
            "results": [
                {
                    "title": f"Mock result for: {query}",
                    "url": f"https://example.com/search?q={query}",
                    "snippet": (
                        f"This is a mock search result for '{query}'. "
                        "Configure a real search function via the "
                        "WebSearchTool constructor to use this tool."
                    ),
                }
            ]
        })


class FileReadTool(Tool):
    """Read the contents of a file from disk with path validation."""

    name = "file_read"
    description = "Read the contents of a file from the local filesystem."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute or relative path to the file",
            },
        },
        "required": ["path"],
    }

    def __init__(self, allowed_base_path: Optional[str] = None):
        super().__init__()
        self._allowed_base_path = allowed_base_path

    def _resolve_path(self, path: str) -> str:
        abs_path = os.path.abspath(os.path.normpath(path))
        if self._allowed_base_path:
            base = os.path.abspath(self._allowed_base_path)
            if not abs_path.startswith(base + os.sep) and abs_path != base:
                raise ToolError(
                    f"Path '{path}' resolves outside the allowed base directory. "
                    f"Allowed base: {base}"
                )
        return abs_path

    def execute(self, path: str) -> str:
        abs_path = self._resolve_path(path)
        if not os.path.exists(abs_path):
            raise ToolError(f"File not found: {path}")
        if not os.path.isfile(abs_path):
            raise ToolError(f"Path is not a file: {path}")
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise ToolError(f"Failed to read file: {e}")


class FileWriteTool(Tool):
    """Write content to a file on disk with path validation."""

    name = "file_write"
    description = "Write content to a file on the local filesystem."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute or relative path to the file",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file",
            },
        },
        "required": ["path", "content"],
    }

    def __init__(self, allowed_base_path: Optional[str] = None):
        super().__init__()
        self._allowed_base_path = allowed_base_path

    def _resolve_path(self, path: str) -> str:
        abs_path = os.path.abspath(os.path.normpath(path))
        if self._allowed_base_path:
            base = os.path.abspath(self._allowed_base_path)
            if not abs_path.startswith(base + os.sep) and abs_path != base:
                raise ToolError(
                    f"Path '{path}' resolves outside the allowed base directory. "
                    f"Allowed base: {base}"
                )
        return abs_path

    def execute(self, path: str, content: str) -> str:
        abs_path = self._resolve_path(path)
        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            return json.dumps({
                "status": "written",
                "path": path,
                "bytes": len(content),
            })
        except Exception as e:
            raise ToolError(f"Failed to write file: {e}")


class PythonExecuteTool(Tool):
    """Execute Python code snippets with security restrictions.

    Blocks imports of os, subprocess, sys, and other system-level modules.
    Uses a threading-based timeout to prevent runaway execution.
    """

    name = "python_execute"
    description = (
        "Execute a Python code snippet and return the output. "
        "Useful for calculations, data processing, and scripting. "
        "System-level modules (os, subprocess, sys) are blocked. "
        "Includes a configurable timeout (default 5 seconds)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to execute",
            },
            "timeout": {
                "type": "integer",
                "description": (
                    "Maximum execution time in seconds (default: 5, max: 30)"
                ),
            },
        },
        "required": ["code"],
    }

    BLOCKED_IMPORTS = [
        "os", "subprocess", "sys", "shutil", "signal", "ctypes",
        "socket", "http", "urllib", "requests", "importlib",
        "importlib_metadata", "atexit", "code", "codeop",
        "compileall", "distutils", "gc", "inspect", "linecache",
        "multiprocessing", "pickle", "pkgutil", "platform",
        "pprint", "pstats", "resource", "runpy", "sysconfig",
        "tabnanny", "tempfile", "threading", "traceback",
        "tracemalloc", "unittest", "warnings", "weakref",
        "webbrowser", "zipimport", "zipfile", "tarfile",
        "argparse", "getopt", "optparse",
    ]

    ALLOWED_BUILTINS = {
        "abs": abs, "all": all, "any": any, "ascii": ascii,
        "bool": bool, "bytearray": bytearray, "bytes": bytes,
        "callable": callable, "chr": chr, "complex": complex,
        "dict": dict, "dir": dir, "divmod": divmod,
        "enumerate": enumerate,
        "filter": filter, "float": float, "format": format,
        "frozenset": frozenset,
        "getattr": getattr, "globals": globals,
        "hasattr": hasattr, "hash": hash, "hex": hex,
        "id": id, "input": input, "int": int,
        "isinstance": isinstance, "issubclass": issubclass,
        "iter": iter,
        "len": len, "list": list, "locals": locals,
        "map": map, "max": max, "min": min,
        "next": next,
        "object": object, "oct": oct, "ord": ord,
        "pow": pow, "print": print,
        "range": range, "repr": repr, "reversed": repr,
        "round": round,
        "set": set, "slice": slice, "sorted": sorted,
        "str": str, "sum": sum,
        "tuple": tuple, "type": type,
        "vars": vars,
        "zip": zip,
    }

    ALLOWED_MODULES = {
        "math": math, "json": json, "re": re,
    }

    def __init__(self):
        super().__init__()

    def _check_imports(self, code: str) -> None:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ToolError(f"Invalid Python syntax: {e}")

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_module = alias.name.split(".")[0]
                    if top_module in self.BLOCKED_IMPORTS:
                        raise ToolError(
                            f"Import of '{alias.name}' is not allowed "
                            f"for security reasons"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                top_module = node.module.split(".")[0]
                if top_module in self.BLOCKED_IMPORTS:
                    raise ToolError(
                        f"Import from '{node.module}' is not allowed "
                        f"for security reasons"
                    )
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                    if node.args:
                        try:
                            mod = node.args[0].value if isinstance(node.args[0], ast.Constant) else ""
                            if mod in self.BLOCKED_IMPORTS:
                                raise ToolError(
                                    f"Import of '{mod}' is not allowed "
                                    f"for security reasons"
                                )
                        except (AttributeError, IndexError):
                            pass

    def execute(self, code: str, timeout: int = 5) -> str:
        timeout = min(max(timeout, 1), 30)
        self._check_imports(code)
        result: Dict[str, str] = {"stdout": "", "error": ""}
        event = threading.Event()

        def run_code():
            try:
                compiled = compile(code, "<exec>", "exec")
                safe_globals: Dict[str, Any] = {
                    "__builtins__": self.ALLOWED_BUILTINS,
                    "__name__": "__main__",
                }
                safe_globals.update(self.ALLOWED_MODULES)
                stdout_capture = io.StringIO()
                import sys as _sys
                old_stdout = _sys.stdout
                old_stderr = _sys.stderr
                try:
                    _sys.stdout = stdout_capture
                    _sys.stderr = stdout_capture
                    exec(compiled, safe_globals)
                finally:
                    _sys.stdout = old_stdout
                    _sys.stderr = old_stderr
                    event.set()
                captured = stdout_capture.getvalue()
                if captured:
                    result["stdout"] = captured
            except Exception as e:
                result["error"] = str(e)
                event.set()

        thread = threading.Thread(target=run_code, daemon=True)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            raise ToolError(
                f"Code execution timed out after {timeout} seconds"
            )

        if result["error"]:
            return json.dumps({"error": result["error"]})
        if result["stdout"]:
            return result["stdout"]
        return json.dumps({"result": "Code executed successfully (no output)"})


class ShellTool(Tool):
    """Run shell commands on the local system.

    Disabled by default for security reasons. Must be explicitly enabled
    by passing allow_shell=True.
    """

    name = "shell"
    description = (
        "Execute a shell command on the local system. "
        "Disabled by default for security reasons."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute",
            },
            "timeout": {
                "type": "integer",
                "description": (
                    "Maximum execution time in seconds (default: 30)"
                ),
            },
        },
        "required": ["command"],
    }

    def __init__(self, allow_shell: bool = False):
        super().__init__()
        self._allow_shell = allow_shell

    def execute(self, command: str, timeout: int = 30) -> str:
        if not self._allow_shell:
            raise ToolError(
                "Shell execution is disabled. "
                "Initialize ShellTool with allow_shell=True to enable."
            )
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output_parts = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                output_parts.append(result.stderr)
            if output_parts:
                return "".join(output_parts)
            return json.dumps({
                "status": "completed",
                "returncode": result.returncode,
            })
        except subprocess.TimeoutExpired:
            raise ToolError(
                f"Shell command timed out after {timeout} seconds"
            )
        except Exception as e:
            raise ToolError(f"Shell command failed: {e}")
