class ZoyaError(Exception):
    def __init__(self, message: str, line: int = 0, col: int = 0, file: str = "") -> None:
        self.line = line
        self.col = col
        self.file = file
        super().__init__(self._format(message))

    def _format(self, message: str) -> str:
        parts = []
        if self.file:
            parts.append(f"File: {self.file}")
        if self.line:
            parts.append(f"Line {self.line}")
        if self.col:
            parts.append(f"Column {self.col}")
        header = ", ".join(parts)
        if header:
            return f"{type(self).__name__} [{header}]: {message}"
        return f"{type(self).__name__}: {message}"


class LexError(ZoyaError):
    pass


class ParseError(ZoyaError):
    pass


class RuntimeError_(ZoyaError):
    pass


class InterpreterError(RuntimeError_):
    pass


class ReturnException(Exception):
    def __init__(self, value: object = None) -> None:
        self.value = value


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass
