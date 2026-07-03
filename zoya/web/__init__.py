"""Zoya 4.0 Web Framework module.

Exposes the Web class and related components for creating web applications.
"""

from typing import Any, Callable, Dict, List, Awaitable

from .router import Router
from .response import (
    ResponseData,
    create_success,
    create_error,
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
)
from .middleware import (
    BaseMiddleware,
    LoggingMiddleware,
    AuthMiddleware,
    ErrorHandlingMiddleware,
)


class Request:
    """Minimal request abstraction."""

    def __init__(self, scope: Dict[str, Any], receive: Callable) -> None:
        self.scope = scope
        self.method = scope.get("method", "GET")
        self.path = scope.get("path", "/")


class Response:
    """HTTP response wrapper."""

    def __init__(self, content: str = "", status: int = 200, headers: Dict[str, str] = None) -> None:
        self.content = content
        self.status = status
        self.headers = headers or {}


class Web:
    """Main web application container."""

    def __init__(self) -> None:
        self.router = Router()
        self.middleware_stack: List[BaseMiddleware] = []

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

    async def _asgi_app(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        if scope.get("type") != "http":
            return

        request = Request(scope, receive)

        handler = self.router.handle(request.method, request.path, request)
        if isinstance(handler, ResponseData):
            await self._send_response(handler, send)
        elif isinstance(handler, dict):
            response = create_success(handler)
            await self._send_response(response, send)
        elif isinstance(handler, str):
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

        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [],
        })
        await send({
            "type": "http.response.body",
            "body": str(response.get("data", "")).encode(),
            "more_body": False,
        })

    async def _send_obj_response(self, response: Response, send: Callable) -> None:
        await send({
            "type": "http.response.start",
            "status": response.status,
            "headers": [(k, v) for k, v in response.headers.items()],
        })
        await send({
            "type": "http.response.body",
            "body": response.content.encode(),
            "more_body": False,
        })


def create_app() -> Web:
    """Factory to create a new Web application."""
    app = Web()
    app.route("GET", "/", lambda: "Hello, World!")
    return app


def create_web_app() -> Web:
    """Convenience function to create a web app."""
    return create_app()


# -------------------- Unit Tests --------------------
async def test_router() -> None:
    """Test router functionality."""
    app = Web()
    app.route("GET", "/test", lambda: "test response")
    scope = {"type": "http", "method": "GET", "path": "/test"}

    async def mock_receive() -> None:
        pass

    async def mock_send(msg: Any) -> None:
        pass

    await app._asgi_app(scope, mock_receive, mock_send)
    print("Router test completed")


def test_response_functions() -> None:
    """Test response creation functions."""
    success = create_success("data", meta={"page": 1})
    assert success["success"] is True
    assert success["data"] == "data"
    assert success["error"] is None
    assert success["meta"] == {"page": 1}

    error = create_error("Invalid input", status=HTTP_400_BAD_REQUEST, meta={"field": "email"})
    assert error["success"] is False
    assert error["error"] == "Invalid input"
    assert error["meta"] == {"field": "email"}


if __name__ == "__main__":
    test_response_functions()
