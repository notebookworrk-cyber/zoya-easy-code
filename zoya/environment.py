"""Environment (scope) management for variable storage in Zoya."""

from __future__ import annotations

from typing import Any


class Environment:
    """Manages variable scoping with parent-child chain semantics."""

    def __init__(self, parent: Environment | None = None) -> None:
        self._vars: dict[str, Any] = {}
        self.parent = parent

    def define(self, name: str, value: Any) -> None:
        self._vars[name] = value

    def get(self, name: str) -> Any:
        if name in self._vars:
            return self._vars[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise NameError(f"'{name}' is not defined")

    def set(self, name: str, value: Any) -> None:
        if name in self._vars:
            self._vars[name] = value
        elif self.parent is not None:
            if self.parent.has(name):
                self.parent.set(name, value)
            else:
                self._vars[name] = value
        else:
            self._vars[name] = value

    def has(self, name: str) -> bool:
        if name in self._vars:
            return True
        if self.parent is not None:
            return self.parent.has(name)
        return False

    def __repr__(self) -> str:
        return f"Environment({self._vars})"
