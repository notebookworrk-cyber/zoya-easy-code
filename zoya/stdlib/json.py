from __future__ import annotations

import json as _json
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    funcs = {
        "load": lambda path: _json.load(open(path, "r", encoding="utf-8")),
        "save": lambda data, path: _json.dump(data, open(path, "w", encoding="utf-8"), indent=2),
        "dumps": lambda data: _json.dumps(data, indent=2),
        "loads": lambda s: _json.loads(s),
    }

    return ZoyaModule("json", funcs)
