"""Zoya stdlib time module."""

from __future__ import annotations

import time as _time
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    funcs = {
        "sleep": _time.sleep,
        "time": _time.time,
        "clock": _time.perf_counter,
        "strftime": _time.strftime,
        "localtime": _time.localtime,
        "gmtime": _time.gmtime,
    }

    return ZoyaModule("time", funcs)
