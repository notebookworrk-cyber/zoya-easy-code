from __future__ import annotations

import os as _os
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    def read(path: str) -> str:
        with open(path, encoding="utf-8") as f:
            return f.read()

    def write(path: str, content: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def append(path: str, content: str) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)

    def exists(path: str) -> bool:
        return _os.path.exists(path)

    def delete(path: str) -> None:
        _os.remove(path)

    def mkdir(path: str) -> None:
        _os.makedirs(path, exist_ok=True)

    def listdir(path: str = ".") -> list[str]:
        return _os.listdir(path)

    funcs = {
        "read": read,
        "write": write,
        "append": append,
        "exists": exists,
        "delete": delete,
        "mkdir": mkdir,
        "listdir": listdir,
        "isdir": _os.path.isdir,
        "isfile": _os.path.isfile,
        "abspath": _os.path.abspath,
        "join": _os.path.join,
        "dirname": _os.path.dirname,
        "basename": _os.path.basename,
        "size": lambda path: _os.path.getsize(path),
    }

    return ZoyaModule("file", funcs)
