"""Zoya stdlib regex module."""

from __future__ import annotations

import re as _re
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    def match(pattern: str, text: str) -> str | None:
        try:
            m = _re.match(pattern, text)
            return m.group(0) if m else None
        except Exception as e:
            return f"Error: {e}"

    def search(pattern: str, text: str) -> str | None:
        try:
            m = _re.search(pattern, text)
            return m.group(0) if m else None
        except Exception as e:
            return f"Error: {e}"

    def findall(pattern: str, text: str) -> list[str]:
        try:
            return _re.findall(pattern, text)
        except Exception as e:
            return [f"Error: {e}"]

    def split(pattern: str, text: str) -> list[str]:
        try:
            return _re.split(pattern, text)
        except Exception as e:
            return [f"Error: {e}"]

    def replace(pattern: str, repl: str, text: str) -> str:
        try:
            return _re.sub(pattern, repl, text)
        except Exception as e:
            return f"Error: {e}"

    def compile(pattern: str) -> Any:
        try:
            return _re.compile(pattern)
        except Exception as e:
            return f"Error: {e}"

    funcs = {
        "match": match,
        "search": search,
        "findall": findall,
        "split": split,
        "replace": replace,
        "compile": compile,
    }

    return ZoyaModule("regex", funcs)
