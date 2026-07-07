"""Zoya stdlib random module."""

from __future__ import annotations

import random as _random
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    funcs = {
        "random": _random.random,
        "randint": _random.randint,
        "uniform": _random.uniform,
        "choice": _random.choice,
        "shuffle": _random.shuffle,
        "sample": _random.sample,
        "seed": _random.seed,
        "gauss": _random.gauss,
        "randrange": _random.randrange,
    }

    return ZoyaModule("random", funcs)
