from __future__ import annotations

from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    funcs = {
        "print": lambda *args, **kwargs: print(*args, **kwargs),
        "input": lambda prompt="": input(prompt),
        "format": lambda s, *args: s % args if args else s,
    }

    return ZoyaModule("io", funcs)
