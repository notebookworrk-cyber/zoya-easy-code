from __future__ import annotations

import contextlib
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    def _request(
        method: str, url: str, data: str = "", headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        try:
            from urllib.request import Request, urlopen

            if headers is None:
                headers = {}
            full_headers = {"User-Agent": "Zoya/2.0"}
            full_headers.update(headers)

            data_bytes = None
            if data and method in ("POST", "PUT"):
                data_bytes = data.encode("utf-8")

            req = Request(url, data=data_bytes, headers=full_headers, method=method)
            with urlopen(req, timeout=30) as response:
                body = response.read().decode("utf-8")
                return {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body": body,
                }
        except Exception as e:
            return {"status": 0, "headers": {}, "body": f"Error: {e}"}

    def get(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        return _request("GET", url, headers=headers)

    def post(
        url: str, data: str = "", headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        return _request("POST", url, data, headers)

    def put(
        url: str, data: str = "", headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        return _request("PUT", url, data, headers)

    def delete(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        return _request("DELETE", url, headers=headers)

    def json(url: str, data: Any = None, method: str = "GET") -> dict[str, Any]:
        import json as _json

        payload = _json.dumps(data) if data is not None else ""
        headers = {"Content-Type": "application/json"}
        result = _request(method, url, payload, headers)
        if result["status"] != 0 and result["body"]:
            with contextlib.suppress(Exception):
                result["body"] = _json.loads(result["body"])
        return result

    funcs = {
        "get": get,
        "post": post,
        "put": put,
        "delete": delete,
        "json": json,
    }

    return ZoyaModule("http", funcs)
