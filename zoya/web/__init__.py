"""Zoya 4.0 Web Framework module.

Exposes the Web class and related components for creating web applications.
"""

from collections.abc import Callable
from typing import Any

from .middleware import (
    AuthMiddleware as AuthMiddleware,
    BaseMiddleware,
    ErrorHandlingMiddleware as ErrorHandlingMiddleware,
    LoggingMiddleware as LoggingMiddleware,
)
from .response import (
    HTTP_200_OK as HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
    ResponseData,
    create_error,
    create_success,
)
from .router import Router

__all__ = [
    "AuthMiddleware",
    "BaseMiddleware",
    "ErrorHandlingMiddleware",
    "HTTP_200_OK",
    "HTTP_400_BAD_REQUEST",
    "HTTP_401_UNAUTHORIZED",
    "HTTP_403_FORBIDDEN",
    "HTTP_404_NOT_FOUND",
    "HTTP_500_INTERNAL_SERVER_ERROR",
    "LoggingMiddleware",
    "Request",
    "Response",
    "ResponseData",
    "Router",
    "Web",
    "create_app",
    "create_error",
    "create_success",
    "create_web_app",
]


class Request:
    """Minimal request abstraction."""

    def __init__(self, scope: dict[str, Any], receive: Callable) -> None:
        self.scope = scope
        self.method = scope.get("method", "GET")
        self.path = scope.get("path", "/")


class Response:
    """HTTP response wrapper."""

    def __init__(
        self, content: str = "", status: int = 200, headers: dict[str, str] = None
    ) -> None:
        self.content = content
        self.status = status
        self.headers = headers or {}


class Web:
    """Main web application container."""

    def __init__(self) -> None:
        self.router = Router()
        self.middleware_stack: list[BaseMiddleware] = []

    def use(self, middleware: BaseMiddleware) -> None:
        """Register a middleware component."""
        self.middleware_stack.append(middleware)

    def route(self, method: str, path: str, handler: Callable) -> None:
        """Register a route with its handler."""
        self.router.route(method, path, handler)

    def run(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """Launch the web server."""
        import uvicorn

        uvicorn.run(self._asgi_app, host=host, port=port)

    async def _asgi_app(self, scope: dict[str, Any], receive: Callable, send: Callable) -> None:
        if scope.get("type") != "http":
            return

        request = Request(scope, receive)

        handler = self.router.handle(request.method, request.path, request)
        if isinstance(handler, ResponseData):
            await self._send_response(handler, send)
        elif isinstance(handler, (dict, str)):
            response = create_success(handler)
            await self._send_response(response, send)
        elif isinstance(handler, Response):
            await self._send_obj_response(handler, send)
        else:
            response = handler()
            await self._send_response(response, send)

    async def _send_response(self, response: ResponseData, send: Callable) -> None:
        status = 200
        if response.get("meta") and isinstance(response["meta"], dict):
            status = response["meta"].get("status", 200)

        await send({"type": "http.response.start", "status": status, "headers": []})
        await send(
            {
                "type": "http.response.body",
                "body": str(response.get("data", "")).encode(),
                "more_body": False,
            }
        )

    async def _send_obj_response(self, response: Response, send: Callable) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": response.status,
                "headers": [(k, v) for k, v in response.headers.items()],
            }
        )
        await send(
            {"type": "http.response.body", "body": response.content.encode(), "more_body": False}
        )


def create_app() -> Web:
    """Factory to create a new Web application."""
    app = Web()
    app.route("GET", "/", lambda: "Hello, World!")
    return app


def create_web_app() -> Web:
    """Convenience function to create a web app."""
    return create_app()
