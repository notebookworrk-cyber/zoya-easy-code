from __future__ import annotations

from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    def deque(items: list[Any] | None = None) -> Any:
        from collections import deque as _deque

        return _deque(items) if items else _deque()

    def counter(items: list[Any]) -> dict[Any, int]:
        from collections import Counter

        return dict(Counter(items))

    def defaultdict(default: Any) -> dict:
        from collections import defaultdict as _dd

        callable_default = default if callable(default) else lambda: default
        return _dd(callable_default)

    def namedtuple(name: str, fields: str | list[str]) -> Any:
        from collections import namedtuple as _nt

        try:
            if isinstance(fields, str):
                field_list = [f.strip() for f in fields.split(",") if f.strip()]
            else:
                field_list = list(fields)
            return _nt(name, field_list)
        except Exception as e:
            return f"Error: {e}"

    def ordered_dict(pairs: list[tuple[Any, Any]] | None = None) -> dict:
        from collections import OrderedDict

        return OrderedDict(pairs) if pairs else OrderedDict()

    funcs = {
        "deque": deque,
        "counter": counter,
        "defaultdict": defaultdict,
        "namedtuple": namedtuple,
        "ordered_dict": ordered_dict,
    }

    return ZoyaModule("collections", funcs)
