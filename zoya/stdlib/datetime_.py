"""Zoya stdlib datetime module."""

from __future__ import annotations

import datetime as _dt
import time as _time
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    def now() -> str:
        return _dt.datetime.now().isoformat()

    def today() -> str:
        return _dt.date.today().isoformat()

    def from_string(s: str, fmt: str = "%Y-%m-%d") -> str:
        try:
            return _dt.datetime.strptime(s, fmt).isoformat()
        except Exception as e:
            return f"Error: {e}"

    def format_dt(dt: str, fmt: str = "%Y-%m-%d") -> str:
        try:
            d = _dt.datetime.fromisoformat(dt)
            return d.strftime(fmt)
        except Exception as e:
            return f"Error: {e}"

    def add(dt: str, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> str:
        try:
            d = _dt.datetime.fromisoformat(dt)
            delta = _dt.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            return (d + delta).isoformat()
        except Exception as e:
            return f"Error: {e}"

    def diff(dt1: str, dt2: str) -> float:
        try:
            d1 = _dt.datetime.fromisoformat(dt1)
            d2 = _dt.datetime.fromisoformat(dt2)
            return (d1 - d2).total_seconds()
        except Exception:
            return 0.0

    def timestamp() -> float:
        return _time.time()

    funcs = {
        "now": now,
        "today": today,
        "from_string": from_string,
        "format": format_dt,
        "add": add,
        "diff": diff,
        "timestamp": timestamp,
    }

    return ZoyaModule("datetime", funcs)
