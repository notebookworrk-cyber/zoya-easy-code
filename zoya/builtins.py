from __future__ import annotations

import random
import time
from typing import Any

from .environment import Environment


def zoya_print(*args: Any, sep: str = " ", end: str = "\n") -> None:
    print(*args, sep=sep, end=end)


def zoya_input(prompt: str = "") -> str:
    return input(prompt)


def zoya_len(obj: Any) -> int:
    return len(obj)


def zoya_type(obj: Any) -> str:
    return type(obj).__name__


def zoya_int(x: Any) -> int:
    return int(x)


def zoya_float(x: Any) -> float:
    return float(x)


def zoya_str(x: Any) -> str:
    return str(x)


def zoya_bool(x: Any) -> bool:
    return bool(x)


def zoya_range(*args: int) -> list[int]:
    return list(range(*args))


def zoya_abs(x: float) -> float:
    return abs(x)


def zoya_round(x: float, ndigits: int = 0) -> float:
    return round(x, ndigits)


def zoya_min(*args: Any) -> Any:
    if not args:
        raise TypeError("min() expects at least one argument")
    return min(args)


def zoya_max(*args: Any) -> Any:
    if not args:
        raise TypeError("max() expects at least one argument")
    return max(args)


def zoya_random(*args: float) -> float:
    if not args:
        return random.random()
    if len(args) == 1:
        return random.uniform(0, args[0])
    return random.uniform(args[0], args[1])


def zoya_sleep(seconds: float) -> None:
    time.sleep(seconds)


def zoya_list(*args: Any) -> list[Any]:
    if len(args) == 1 and hasattr(args[0], "__iter__"):
        return list(args[0])
    return list(args)


def zoya_dict(*args: Any, **kwargs: Any) -> dict[str, Any]:
    if args:
        if len(args) == 1:
            return dict(args[0])
        raise TypeError(f"dict() takes at most 1 positional argument ({len(args)} given)")
    return dict(kwargs)


def zoya_sum(iterable: list[Any]) -> Any:
    return sum(iterable)


def zoya_hex(x: int) -> str:
    return hex(x)


def zoya_bin(x: int) -> str:
    return bin(x)


BUILTIN_FUNCTIONS: dict[str, Any] = {
    "print": zoya_print,
    "input": zoya_input,
    "len": zoya_len,
    "type": zoya_type,
    "int": zoya_int,
    "float": zoya_float,
    "str": zoya_str,
    "bool": zoya_bool,
    "range": zoya_range,
    "abs": zoya_abs,
    "round": zoya_round,
    "min": zoya_min,
    "max": zoya_max,
    "random": zoya_random,
    "sleep": zoya_sleep,
    "list": zoya_list,
    "dict": zoya_dict,
    "sum": zoya_sum,
    "hex": zoya_hex,
    "bin": zoya_bin,
    "True": True,
    "False": False,
    "None": None,
}

STRING_METHODS: dict[str, Any] = {
    "upper": lambda s: s.upper(),
    "lower": lambda s: s.lower(),
    "strip": lambda s, chars=None: s.strip(chars) if chars is not None else s.strip(),
    "replace": lambda s, old, new: s.replace(old, new),
    "split": lambda s, sep=None: s.split(sep) if sep else s.split(),
    "startswith": lambda s, prefix: s.startswith(prefix),
    "endswith": lambda s, suffix: s.endswith(suffix),
    "contains": lambda s, sub: sub in s,
}

LIST_METHODS: dict[str, Any] = {
    "append": lambda lst, item: lst.append(item) or lst,
    "remove": lambda lst, item: lst.remove(item) or lst,
    "pop": lambda lst, index=-1: lst.pop(index),
    "clear": lambda lst: lst.clear() or lst,
    "insert": lambda lst, index, item: lst.insert(index, item) or lst,
    "sort": lambda lst: lst.sort() or lst,
    "reverse": lambda lst: lst.reverse() or lst,
    "length": lambda lst: len(lst),
    "copy": lambda lst: lst.copy(),
}

DICT_METHODS: dict[str, Any] = {
    "keys": lambda d: list(d.keys()),
    "values": lambda d: list(d.values()),
    "items": lambda d: list(d.items()),
    "contains": lambda d, key: key in d,
    "get": lambda d, key, default=None: d.get(key, default),
    "copy": lambda d: d.copy(),
    "clear": lambda d: d.clear() or d,
}


def register_builtins(env: Environment) -> None:
    for name, func in BUILTIN_FUNCTIONS.items():
        env.define(name, func)
