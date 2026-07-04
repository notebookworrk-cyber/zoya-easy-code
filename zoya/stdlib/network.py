from __future__ import annotations

from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    def get(url: str, timeout: int = 10) -> str:
        try:
            from urllib.request import Request, urlopen

            req = Request(url, headers={"User-Agent": "Zoya/1.0"})
            with urlopen(req, timeout=timeout) as response:
                return response.read().decode("utf-8")
        except Exception as e:
            return f"Error: {e}"

    def post(url: str, data: str = "", content_type: str = "application/json") -> str:
        try:
            from urllib.request import Request, urlopen

            data_bytes = data.encode("utf-8") if data else None
            req = Request(
                url,
                data=data_bytes,
                headers={
                    "User-Agent": "Zoya/1.0",
                    "Content-Type": content_type,
                },
            )
            with urlopen(req, timeout=10) as response:
                return response.read().decode("utf-8")
        except Exception as e:
            return f"Error: {e}"

    def download(url: str, path: str) -> str:
        try:
            from urllib.request import Request, urlopen

            req = Request(url, headers={"User-Agent": "Zoya/1.0"})
            with urlopen(req, timeout=30) as response:
                data = response.read()
            with open(path, "wb") as f:
                f.write(data)
            return f"Downloaded to {path}"
        except Exception as e:
            return f"Error: {e}"

    funcs = {
        "get": get,
        "post": post,
        "download": download,
    }

    return ZoyaModule("network", funcs)
