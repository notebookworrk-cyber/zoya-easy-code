"""Zoya 4.0 Router module.

Provides a Router class for defining and matching HTTP routes with
support for path parameters and middleware.
"""

import re
from typing import Callable, Dict, List, Tuple, Any, Optional


Handler = Callable[..., Any]


class Route:
    """Represents a single route."""

    def __init__(self, method: str, pattern: re.Pattern, handler: Handler) -> None:
        self.method = method.upper()
        self.regex = pattern
        self.handler = handler

    def match(self, path: str) -> Tuple[bool, Dict[str, str]]:
        m = self.regex.match(path)
        return (True, m.groupdict()) if m else (False, {})


class Router:
    """Router for Zoya 4.0 with route registration, matching and middleware."""

    def __init__(self) -> None:
        self._routes: List[Route] = []
        self._middleware: List[Callable[[Handler], Handler]] = []

    def use(self, middleware: Callable[[Handler], Handler]) -> None:
        """Register a middleware that wraps the next handler."""
        self._middleware.append(middleware)

    def route(self, method: str, path: str, handler: Optional[Handler] = None) -> Any:
        """Register a route. Can be used as a decorator or directly."""
        method = method.upper()
        pattern = re.compile("^" + self._escape_path(path) + "$")

        if handler is not None:
            self._routes.append(Route(method, pattern, handler))
            return handler

        def decorator(fn: Handler) -> Handler:
            self._routes.append(Route(method, pattern, fn))
            return fn

        return decorator

    def _escape_path(self, path: str) -> str:
        """Convert path string to a regex pattern, supporting {name} placeholders."""
        parts: List[str] = []
        i = 0
        while i < len(path):
            if path[i] == "{":
                j = path.find("}", i)
                if j == -1:
                    parts.append(re.escape(path[i:]))
                    break
                name = path[i + 1 : j]
                parts.append(f"(?P<{name}>[^/]+)")
                i = j + 1
            else:
                parts.append(re.escape(path[i]))
                i += 1
        return "".join(parts)

    def handle(self, method: str, path: str, request: Any = None) -> Handler:
        """Find a matching route; raises KeyError if none."""
        method = method.upper()
        for route in self._routes:
            if route.method == method:
                ok, params = route.match(path)
                if ok:
                    return route.handler
        # Return None handler if no match
        return lambda: "Not Found"

    def match(self, method: str, path: str) -> Tuple[Handler, Dict[str, str]]:
        """Find a matching route; raises KeyError if none."""
        method = method.upper()
        for route in self._routes:
            if route.method == method:
                ok, params = route.match(path)
                if ok:
                    return route.handler, params
        raise KeyError(f"No route matched for {method} {path}")
