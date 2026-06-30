from __future__ import annotations

import math as _math
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    funcs = {
        "sin": _math.sin,
        "cos": _math.cos,
        "tan": _math.tan,
        "asin": _math.asin,
        "acos": _math.acos,
        "atan": _math.atan,
        "atan2": _math.atan2,
        "sqrt": _math.sqrt,
        "log": _math.log,
        "log10": _math.log10,
        "ceil": _math.ceil,
        "floor": _math.floor,
        "pow": _math.pow,
        "pi": _math.pi,
        "e": _math.e,
        "inf": _math.inf,
        "nan": _math.nan,
        "degrees": _math.degrees,
        "radians": _math.radians,
        "factorial": _math.factorial,
        "gcd": _math.gcd,
    }

    return ZoyaModule("math", funcs)
