from __future__ import annotations

import os as _os
import sys as _sys
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    def exit(code: int = 0) -> None:
        _sys.exit(code)

    def env(name: str) -> str:
        return _os.environ.get(name, "")

    def set_env(name: str, value: str) -> str:
        try:
            _os.environ[name] = value
            return f"Set {name}={value}"
        except Exception as e:
            return f"Error: {e}"

    def cwd() -> str:
        return _os.getcwd()

    def chdir(path: str) -> str:
        try:
            _os.chdir(path)
            return f"Changed to {path}"
        except Exception as e:
            return f"Error: {e}"

    def platform() -> str:
        return _sys.platform

    def cpu_count() -> int:
        return _os.cpu_count() or 0

    def memory() -> dict[str, Any]:
        try:
            import psutil

            mem = psutil.virtual_memory()
            return {
                "total": mem.total,
                "available": mem.available,
                "percent": mem.percent,
                "used": mem.used,
            }
        except ImportError:
            return {"error": "psutil not installed"}
        except Exception as e:
            return {"error": str(e)}

    def pid() -> int:
        return _os.getpid()

    funcs = {
        "exit": exit,
        "env": env,
        "set_env": set_env,
        "cwd": cwd,
        "chdir": chdir,
        "platform": platform,
        "cpu_count": cpu_count,
        "memory": memory,
        "pid": pid,
    }

    return ZoyaModule("system", funcs)
