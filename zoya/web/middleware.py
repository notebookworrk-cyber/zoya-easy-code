"""Zoya 4.0 Middleware module.

Provides middleware components for the web framework.
"""

from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Dict, Any


class BaseMiddleware(ABC):
    """Base class for all middleware components in Zoya 4.0.

    Subclasses must implement the __call__ method to define middleware behavior.
    """

    @abstractmethod
    async def __call__(
        self,
        request: Dict[str, Any],
        call_next: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Process the request and return a response."""

    def to_handler(
        self, next_handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]:
        """Wrap this middleware around the next handler."""
        async def wrapped(request: Dict[str, Any]) -> Dict[str, Any]:
            return await self(request, next_handler)
        return wrapped


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging requests and responses."""

    async def __call__(
        self,
        request: Dict[str, Any],
        call_next: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        print(f"Request: {request}")
        response = await call_next(request)
        print(f"Response: {response}")
        return response


class AuthMiddleware(BaseMiddleware):
    """Middleware for authentication."""

    def __init__(self, is_authenticated: Callable[[Dict[str, Any]], bool]) -> None:
        self.is_authenticated = is_authenticated

    async def __call__(
        self,
        request: Dict[str, Any],
        call_next: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        if not self.is_authenticated(request):
            return {"error": "Unauthorized", "status": 401}
        return await call_next(request)


class ErrorHandlingMiddleware(BaseMiddleware):
    """Middleware for handling exceptions."""

    async def __call__(
        self,
        request: Dict[str, Any],
        call_next: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        try:
            return await call_next(request)
        except Exception as exc:
            print(f"Error occurred: {exc}")
            return {"error": "Internal Server Error", "status": 500}
