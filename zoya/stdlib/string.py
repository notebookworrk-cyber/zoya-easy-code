from __future__ import annotations

import string as _string_mod
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    funcs = {
        "upper": str.upper,
        "lower": str.lower,
        "capitalize": str.capitalize,
        "title": str.title,
        "strip": str.strip,
        "lstrip": str.lstrip,
        "rstrip": str.rstrip,
        "replace": str.replace,
        "split": str.split,
        "join": lambda sep, items: sep.join(str(i) for i in items),
        "startswith": str.startswith,
        "endswith": str.endswith,
        "contains": lambda s, sub: sub in s,
        "format": str.format,
        "len": len,
        "reverse": lambda s: s[::-1],
        "count": str.count,
        "find": str.find,
        "isdigit": str.isdigit,
        "isalpha": str.isalpha,
        "isalnum": str.isalnum,
        "isspace": str.isspace,
        "islower": str.islower,
        "isupper": str.isupper,
    }

    return ZoyaModule("string", funcs)
