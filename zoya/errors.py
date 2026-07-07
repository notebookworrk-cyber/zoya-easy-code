from __future__ import annotations


class ZoyaError(Exception):
    """Base exception for all Zoya language errors."""

    def __init__(
        self, message: str, line: int = 0, col: int = 0, file: str = "", source: str = ""
    ) -> None:
        self.line = line
        self.col = col
        self.file = file
        self.source = source
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
            base = f"{type(self).__name__} [{header}]: {message}"
        else:
            base = f"{type(self).__name__}: {message}"

        if self.source and self.line > 0:
            lines = self.source.splitlines()
            if 0 < self.line <= len(lines):
                source_line = lines[self.line - 1]
                base += f"\n  {source_line}"
                if self.col > 0:
                    marker = " " * (self.col - 1) + "^"
                    base += f"\n  {marker}"
        return base

    def with_source(self, source: str) -> ZoyaError:
        """Return a new error instance with source code attached."""
        new = type(self)(
            str(self).split(": ", 1)[1] if ": " in str(self) else str(self),
            line=self.line,
            col=self.col,
            file=self.file,
            source=source,
        )
        return new


class LexError(ZoyaError):
    """Lexical analysis error (invalid token, unterminated string, etc.)."""

    pass


class ParseError(ZoyaError):
    """Parsing error (syntax error, unexpected token, etc.)."""

    pass


class RuntimeError_(ZoyaError):
    """Base class for runtime errors."""

    pass


class ZoyaRuntimeError(RuntimeError_):
    """General runtime error (thrown by 'throw' or uncaught exception)."""

    pass


class ZoyaTypeError(RuntimeError_):
    """Type error (invalid operation for type, wrong argument type, etc.)."""

    pass


class InterpreterError(RuntimeError_):
    """Internal interpreter error (should not happen in user code)."""

    pass


class ReturnException(Exception):
    """Control flow exception for return statements."""

    def __init__(self, value: object = None) -> None:
        self.value = value
        super().__init__()


class BreakException(Exception):
    """Control flow exception for break statements."""

    pass


class ContinueException(Exception):
    """Control flow exception for continue statements."""

    pass


class CallFrame:
    """Represents a single frame in the call stack."""

    def __init__(self, func_name: str, file: str = "", line: int = 0, col: int = 0) -> None:
        self.func_name = func_name
        self.file = file
        self.line = line
        self.col = col
        self.parent: CallFrame | None = None

    def __repr__(self) -> str:
        loc = f"{self.file}:{self.line}:{self.col}" if self.file else "unknown"
        return f"  at {self.func_name} ({loc})"


class StackOverflowError(RuntimeError_):
    """Stack overflow error (recursion depth exceeded)."""

    def __init__(
        self,
        message: str = "Maximum call stack depth exceeded (limit: 1000)",
        line: int = 0,
        col: int = 0,
        file: str = "",
        source: str = "",
    ) -> None:
        super().__init__(message, line, col, file, source)


class ZoyaZeroDivisionError(RuntimeError_):
    """Division by zero error."""

    def __init__(
        self,
        message: str = "Division by zero",
        line: int = 0,
        col: int = 0,
        file: str = "",
        source: str = "",
    ) -> None:
        super().__init__(message, line, col, file, source)


class ZoyaNameError(RuntimeError_):
    """Name not defined error."""

    def __init__(
        self, name: str = "", line: int = 0, col: int = 0, file: str = "", source: str = ""
    ) -> None:
        message = f"'{name}' is not defined" if name else "Name is not defined"
        super().__init__(message, line, col, file, source)
        self.name = name


class ZoyaAttributeError(RuntimeError_):
    """Attribute not found error."""

    def __init__(
        self,
        obj_type: str = "",
        attr: str = "",
        line: int = 0,
        col: int = 0,
        file: str = "",
        source: str = "",
    ) -> None:
        if obj_type and attr:
            message = f"'{obj_type}' object has no attribute '{attr}'"
        elif attr:
            message = f"Object has no attribute '{attr}'"
        else:
            message = "Object has no attribute"
        super().__init__(message, line, col, file, source)
        self.obj_type = obj_type
        self.attr = attr


class ZoyaIndexError(RuntimeError_):
    """Index out of range error."""

    def __init__(
        self,
        message: str = "Index out of range",
        line: int = 0,
        col: int = 0,
        file: str = "",
        source: str = "",
    ) -> None:
        super().__init__(message, line, col, file, source)


class ImportCycleError(RuntimeError_):
    """Import cycle detected."""

    def __init__(
        self, cycle: list[str], line: int = 0, col: int = 0, file: str = "", source: str = ""
    ) -> None:
        cycle_str = " -> ".join(cycle)
        message = f"Import cycle detected: {cycle_str}"
        super().__init__(message, line, col, file, source)
        self.cycle = cycle


def format_stack_trace(frames: list[CallFrame]) -> str:
    """Format a list of call frames into a readable stack trace."""
    if not frames:
        return ""
    lines = ["Stack trace (most recent call last):"]
    for frame in reversed(frames):
        loc = f"{frame.file}:{frame.line}:{frame.col}" if frame.file else "unknown location"
        lines.append(f"  {frame.func_name} at {loc}")
    return "\n".join(lines)


def attach_stack_trace(error: ZoyaError, frames: list[CallFrame]) -> ZoyaError:
    """Attach stack trace to an error."""
    error.__cause__ = None
    error.__context__ = None
    trace = format_stack_trace(frames)
    if trace:
        # Create a new error with the trace appended
        new_msg = f"{str(error)}\n{trace}"
        new_error = type(error)(
            new_msg.split(": ", 1)[1] if ": " in new_msg else new_msg,
            line=error.line,
            col=error.col,
            file=error.file,
            source=error.source,
        )
        return new_error
    return error
