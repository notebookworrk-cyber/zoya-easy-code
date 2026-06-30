from __future__ import annotations

from ..ast import (
    ASTNode,
    Assign,
    AssignAttr,
    AssignIndex,
    BinOp,
    Block,
    Boolean,
    Break,
    Call,
    Continue,
    Dict_,
    Function,
    GetAttr,
    Ident,
    If,
    Import,
    Index,
    Input,
    InterpolatedString,
    List_,
    Loop,
    MethodCall,
    Number,
    Print,
    Return,
    Slice,
    String,
    UnaryOp,
    While,
)
from ..lexer import tokenize
from ..parser import parse

_BUILTIN_NAMES: set[str] = {
    "print", "input", "len", "str", "int", "float", "bool", "list",
    "dict", "range", "type", "min", "max", "sum", "abs", "round",
    "open", "read", "write", "split", "join", "map", "filter",
    "append", "pop", "sort", "reverse", "keys", "values", "items",
    "clear", "copy", "count", "index", "insert", "remove", "extend",
    "upper", "lower", "strip", "startswith", "endswith", "replace",
    "find", "format",
}

_IGNORE_NAMES: set[str] = {"_", "__"}


def lint(source: str, filepath: str = "") -> list[dict]:
    issues: list[dict] = []
    lines = source.split("\n")

    _check_line_length(lines, issues)
    _check_trailing_newline(source, lines, issues)
    _check_indentation(lines, issues)

    try:
        tokens = tokenize(source, filepath)
        ast = parse(tokens, filepath)
        _check_unused_vars(ast, issues)
    except Exception:
        pass

    issues.sort(key=lambda i: (i["line"], i["col"]))
    return issues


def _check_line_length(lines: list[str], issues: list[dict]) -> None:
    for i, line in enumerate(lines, 1):
        if len(line) > 100:
            issues.append({
                "line": i,
                "col": 101,
                "message": f"Line too long ({len(line)} > 100 characters)",
                "severity": "warning",
            })


def _check_trailing_newline(source: str, lines: list[str], issues: list[dict]) -> None:
    if not source.endswith("\n") and len(lines) > 0:
        issues.append({
            "line": len(lines),
            "col": len(lines[-1]),
            "message": "No newline at end of file",
            "severity": "style",
        })


def _check_indentation(lines: list[str], issues: list[dict]) -> None:
    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("/*"):
            continue
        indent = line[: len(line) - len(stripped)]
        if "\t" in indent:
            issues.append({
                "line": i,
                "col": 1,
                "message": "Tab character in indentation (use spaces)",
                "severity": "style",
            })
        elif indent and len(indent) % 4 != 0:
            issues.append({
                "line": i,
                "col": 1,
                "message": f"Inconsistent indentation ({len(indent)} spaces, expected multiple of 4)",
                "severity": "style",
            })


def _check_unused_vars(ast: ASTNode, issues: list[dict]) -> None:
    definitions: list[tuple[str, int, int]] = []
    references: set[str] = set()

    def walk(node: ASTNode, in_def: bool = False) -> None:
        if isinstance(node, Assign):
            definitions.append((node.name, node.line, node.col))
            walk(node.expr)
        elif isinstance(node, Function):
            definitions.append((node.name, node.line, node.col))
            for p in node.params:
                definitions.append((p, node.line, node.col))
            walk(node.body)
        elif isinstance(node, Block):
            for s in node.statements:
                walk(s)
        elif isinstance(node, Ident):
            if not in_def:
                references.add(node.name)
        elif isinstance(node, BinOp):
            walk(node.left)
            walk(node.right)
        elif isinstance(node, UnaryOp):
            walk(node.expr)
        elif isinstance(node, Call):
            walk(node.callee)
            for a in node.args:
                walk(a)
        elif isinstance(node, MethodCall):
            walk(node.obj)
            for a in node.args:
                walk(a)
        elif isinstance(node, Index):
            walk(node.obj)
            walk(node.index)
        elif isinstance(node, Slice):
            walk(node.obj)
            if node.start:
                walk(node.start)
            if node.stop:
                walk(node.stop)
            if node.step:
                walk(node.step)
        elif isinstance(node, GetAttr):
            walk(node.obj)
        elif isinstance(node, AssignIndex):
            walk(node.obj)
            walk(node.index)
            walk(node.expr)
        elif isinstance(node, AssignAttr):
            walk(node.obj)
            walk(node.expr)
        elif isinstance(node, Print):
            walk(node.expr)
        elif isinstance(node, Input):
            if node.prompt:
                walk(node.prompt)
        elif isinstance(node, Return):
            if node.expr:
                walk(node.expr)
        elif isinstance(node, If):
            walk(node.cond)
            walk(node.body)
            if node.else_body:
                walk(node.else_body)
        elif isinstance(node, While):
            walk(node.cond)
            walk(node.body)
        elif isinstance(node, Loop):
            walk(node.count)
            walk(node.body)
        elif isinstance(node, List_):
            for e in node.elements:
                walk(e)
        elif isinstance(node, Dict_):
            for k, v in node.pairs:
                walk(k)
                walk(v)
        elif isinstance(node, InterpolatedString):
            for part in node.parts:
                if isinstance(part, (ASTNode, tuple)):
                    if isinstance(part, tuple):
                        walk(part[0])
                    else:
                        walk(part)
        elif isinstance(node, Import):
            pass
        elif isinstance(node, (Number, String, Boolean, Break, Continue)):
            pass

    walk(ast)

    defined_names = {name for name, _, _ in definitions}
    self_referencing = defined_names & references
    for name, line, col in definitions:
        if name in _IGNORE_NAMES or name in _BUILTIN_NAMES:
            continue
        if name not in self_referencing:
            issues.append({
                "line": line,
                "col": col,
                "message": f"Unused variable '{name}'",
                "severity": "warning",
            })
