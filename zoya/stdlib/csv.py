"""Zoya stdlib CSV module."""

from __future__ import annotations

import csv as _csv
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    def read(path: str) -> list[dict[str, str]]:
        try:
            with open(path, encoding="utf-8", newline="") as f:
                reader = _csv.DictReader(f)
                return list(reader)
        except Exception as e:
            return [{"error": str(e)}]

    def write(path: str, rows: list[list[str]]) -> str:
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = _csv.writer(f)
                writer.writerows(rows)
            return f"Written {len(rows)} rows"
        except Exception as e:
            return f"Error: {e}"

    def parse(text: str) -> list[list[str]]:
        try:
            reader = _csv.reader(text.splitlines())
            return list(reader)
        except Exception as e:
            return [["error", str(e)]]

    def format(rows: list[list[str]]) -> str:
        try:
            import io

            buf = io.StringIO()
            writer = _csv.writer(buf)
            writer.writerows(rows)
            return buf.getvalue()
        except Exception as e:
            return f"Error: {e}"

    funcs = {"read": read, "write": write, "parse": parse, "format": format}

    return ZoyaModule("csv", funcs)
