from __future__ import annotations

from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    class _Connection:
        def __init__(self, conn: Any) -> None:
            self._conn = conn
            self._cursor = conn.cursor()

        def execute(self, sql: str, params: list[Any] | None = None) -> str:
            try:
                if params:
                    self._cursor.execute(sql, params)
                else:
                    self._cursor.execute(sql)
                self._conn.commit()
                return f"Executed: {sql}"
            except Exception as e:
                return f"Error: {e}"

        def fetch_all(self) -> list[tuple[Any, ...]]:
            try:
                return self._cursor.fetchall()
            except Exception as e:
                return [("Error", str(e))]

        def fetch_one(self) -> tuple[Any, ...] | None:
            try:
                return self._cursor.fetchone()
            except Exception as e:
                return ("Error", str(e))

        def fetch_many(self, size: int = 1) -> list[tuple[Any, ...]]:
            try:
                return self._cursor.fetchmany(size)
            except Exception as e:
                return [("Error", str(e))]

        def close(self) -> str:
            try:
                self._cursor.close()
                self._conn.close()
                return "Connection closed"
            except Exception as e:
                return f"Error: {e}"

    def connect(path: str) -> _Connection:
        import sqlite3

        try:
            conn = sqlite3.connect(path)
            return _Connection(conn)
        except Exception:
            return None  # type: ignore[return-value]

    funcs = {
        "connect": connect,
    }

    return ZoyaModule("database", funcs)
